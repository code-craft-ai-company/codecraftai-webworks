"""
    Metrics sharing module for the production server.

    The production server runs its requests in several worker processes, and
    each worker counts its own requests in a MetricsCollector. A scrape of the
    metrics endpoint reaches one worker, so the counts of every worker have to
    be added up to answer it. This module does that through a directory the
    workers share:

    - every worker writes a snapshot of its collector to ``worker-<pid>.json``
      (atomically, with a rename): a writer thread does it once per write
      interval while the counts change, and the worker does it before it
      answers a scrape and when it stops, so a scrape sees counts that are at
      most one interval old,
    - when a worker process has ended, the master folds its last snapshot
      into ``retired.json`` and removes the worker file, so counters do not go
      down when workers are recycled and the directory does not fill up,
    - a scrape merges ``retired.json`` and the files of the live workers.

    ``retired.json`` lists the processes it already contains, so a scrape that
    runs while the master folds a worker in counts that worker exactly once.
"""

import json
import logging
import os
import threading

from typing import Any, Dict, Optional, Set, TYPE_CHECKING

from ccai.webworks.prodserver.metricscollector import MetricsCollector

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Default logger for the metrics store
_logger = logging.getLogger("webworks.prodserver.metricsstore")

# File name parts of the snapshots
WORKER_FILE_PREFIX = "worker-"
WORKER_FILE_SUFFIX = ".json"
RETIRED_FILE_NAME = "retired.json"

# Seconds between two snapshots the writer thread of a worker writes
DEFAULT_WRITE_INTERVAL: float = 1.0


class MetricsStore:
    """
        Shares the metrics of the worker processes through a directory.
    """

    def __init__(
        self,
        directory: str,
        config: "ServerConfig",
        write_interval: float = DEFAULT_WRITE_INTERVAL,
    ):
        """
            Construct a MetricsStore.

            :param directory: The directory the snapshots are kept in. It must
                exist and be writable by the worker processes.
            :param config: The server configuration, for the collectors the
                store builds.
            :param write_interval: Seconds between two snapshots written by
                the writer thread.
        """
        self._directory = directory
        self._config = config
        self._write_interval = write_interval
        self._write_lock = threading.Lock()
        self._writer_thread: Optional[threading.Thread] = None
        self._writer_stop = threading.Event()
        return

    @property
    def directory(self) -> str:
        """
            Get the directory of the snapshots.

            :returns: The directory path.
        """
        return self._directory

    def worker_file(self, pid: int) -> str:
        """
            Get the snapshot file of a worker process.

            :param pid: The worker process.

            :returns: The file path.
        """
        rtnval = os.path.join(self._directory, f"{WORKER_FILE_PREFIX}{pid}{WORKER_FILE_SUFFIX}")
        return rtnval

    # =========================================================================
    # Worker side
    # =========================================================================

    def write_snapshot(self, collector: MetricsCollector, pid: Optional[int] = None) -> None:
        """
            Write the snapshot of a worker's collector.

            :param collector: The collector of the worker.
            :param pid: The worker process, the current one when None.
        """
        if pid is None:
            pid = os.getpid()

        state = collector.export_state()

        with self._write_lock:
            self._write_json(self.worker_file(pid), state)

        return

    def start_snapshot_writer(self, collector: MetricsCollector) -> None:
        """
            Start the thread that writes the snapshot of this worker once per
            write interval while its counts change.

            Called in the worker process, after it was forked.

            :param collector: The collector of the worker.
        """
        if self._writer_thread is not None and self._writer_thread.is_alive():
            return

        self._writer_stop = threading.Event()
        self._writer_thread = threading.Thread(
            target=self._write_periodically,
            args=(collector, self._writer_stop),
            name="webworks-metrics-snapshot",
            daemon=True,
        )
        self._writer_thread.start()
        return

    def stop_snapshot_writer(self) -> None:
        """
            Stop the writer thread of this worker and wait for it.
        """
        writer = self._writer_thread
        if writer is None:
            return

        self._writer_stop.set()
        writer.join(timeout=self._write_interval + 5.0)
        self._writer_thread = None
        return

    def _write_periodically(self, collector: MetricsCollector, stop: threading.Event) -> None:
        """
            Body of the writer thread.

            :param collector: The collector of the worker.
            :param stop: Set when the thread is to end.
        """
        last_written_total = collector.get_request_count()

        while not stop.wait(self._write_interval):
            current_total = collector.get_request_count()
            if current_total == last_written_total:
                continue

            try:
                self.write_snapshot(collector)
                last_written_total = current_total
            except OSError as write_err:
                # The next interval tries again; the scrape and the worker
                # exit write their own snapshot as well.
                _logger.warning("Writing the metrics snapshot failed: %s", write_err)

        return

    # =========================================================================
    # Master side
    # =========================================================================

    def retire_worker(self, pid: int) -> None:
        """
            Fold the last snapshot of an ended worker into the retired totals.

            Called by the master, the only process that writes the retired
            file, when it has reaped the worker. The gauges of the worker
            (active connections, its status) are not kept.

            :param pid: The worker process that ended.
        """
        worker_path = self.worker_file(pid)
        worker_state = self._read_json(worker_path)

        retired = self._read_json(os.path.join(self._directory, RETIRED_FILE_NAME))
        if retired is None:
            retired = {"merged_pids": [], "state": {}}

        merged_pids = set(retired.get("merged_pids", []))

        if worker_state is not None and pid not in merged_pids:
            collector = MetricsCollector(self._config)
            collector.merge_state(retired.get("state", {}), include_gauges=False)
            collector.merge_state(worker_state, include_gauges=False)

            merged_pids.add(pid)
            retired = {
                "merged_pids": sorted(merged_pids),
                "state": collector.export_state(),
            }

            self._write_json(os.path.join(self._directory, RETIRED_FILE_NAME), retired)

        if os.path.exists(worker_path):
            os.remove(worker_path)

        return

    # =========================================================================
    # Scrape
    # =========================================================================

    def collect(self) -> MetricsCollector:
        """
            Add up the metrics of every worker, live and ended.

            :returns: A collector holding the totals.
        """
        live_states: Dict[int, Dict[str, Any]] = {}

        for file_name in sorted(os.listdir(self._directory)):
            if not file_name.startswith(WORKER_FILE_PREFIX) or not file_name.endswith(WORKER_FILE_SUFFIX):
                continue

            pid_text = file_name[len(WORKER_FILE_PREFIX):-len(WORKER_FILE_SUFFIX)]
            if not pid_text.isdigit():
                continue

            state = self._read_json(os.path.join(self._directory, file_name))
            if state is not None:
                live_states[int(pid_text)] = state

        # Read after the worker files: the master writes the retired file
        # before it removes a worker file, so a worker missing above is in it.
        retired = self._read_json(os.path.join(self._directory, RETIRED_FILE_NAME))
        merged_pids: Set[int] = set()

        collector = MetricsCollector(self._config)

        if retired is not None:
            merged_pids = set(retired.get("merged_pids", []))
            collector.merge_state(retired.get("state", {}), include_gauges=False)

        for pid, state in live_states.items():
            if pid in merged_pids:
                continue
            collector.merge_state(state, include_gauges=True)

        return collector

    # =========================================================================
    # Files
    # =========================================================================

    def _write_json(self, path: str, data: Dict[str, Any]) -> None:
        """
            Write a JSON file atomically.

            :param path: The file path.
            :param data: The data to write.
        """
        temporary_path = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"

        with open(temporary_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file)

        os.replace(temporary_path, path)
        return

    def _read_json(self, path: str) -> Optional[Dict[str, Any]]:
        """
            Read a JSON file written by _write_json.

            :param path: The file path.

            :returns: The data, or None when the file does not exist (a
                worker that has not written yet, or one that was retired).
        """
        try:
            with open(path, "r", encoding="utf-8") as json_file:
                rtnval = json.load(json_file)
        except FileNotFoundError:
            rtnval = None

        return rtnval
