"""
    Tests for the MetricsStore class.

    The store shares the metrics of the worker processes through a directory:
    each worker writes snapshots, the master folds the snapshot of an ended
    worker into the retired totals, and a scrape adds everything up.
"""

import json
import os
import shutil
import tempfile
import time

from ccai.webworks.prodserver.metricscollector import MetricsCollector
from ccai.webworks.prodserver.metricsstore import RETIRED_FILE_NAME, MetricsStore
from ccai.webworks.prodserver.serverconfig import ServerConfig
from ccai.webworks.prodserver.workerstate import WorkerState


def _collector_with(requests: int, worker_id: int) -> MetricsCollector:
    """
        A collector that counted some GET /x requests of one worker.
    """
    collector = MetricsCollector(ServerConfig())
    for _ in range(requests):
        collector.record_request("/x", "GET", 200, 1.0)
    collector.update_worker_status(worker_id, WorkerState.ACTIVE)
    return collector


def test_collect_adds_up_the_live_workers():
    """
        The snapshots of all live workers are added up.
    """
    directory = tempfile.mkdtemp(prefix="metricsstore-")
    store = MetricsStore(directory, ServerConfig())

    try:
        store.write_snapshot(_collector_with(3, 1), pid=1001)
        store.write_snapshot(_collector_with(4, 2), pid=1002)
        totals = store.collect()
    finally:
        shutil.rmtree(directory)

    if totals.get_request_count() != 7 or totals.get_worker_statuses() != {1: "active", 2: "active"}:
        errmsg = f"Expected 7 requests of two workers, got {totals.get_request_count()} {totals.get_worker_statuses()}"
        raise AssertionError(errmsg)

    return


def test_retired_worker_keeps_its_counts_but_not_its_gauges():
    """
        Counters do not go down when a worker ends; its worker status goes.
    """
    directory = tempfile.mkdtemp(prefix="metricsstore-")
    store = MetricsStore(directory, ServerConfig())

    try:
        store.write_snapshot(_collector_with(3, 1), pid=1001)
        store.write_snapshot(_collector_with(4, 2), pid=1002)
        store.retire_worker(1001)
        totals = store.collect()
        worker_file_left = os.path.exists(store.worker_file(1001))
        with open(os.path.join(directory, RETIRED_FILE_NAME), "r", encoding="utf-8") as retired_file:
            retired = json.load(retired_file)
    finally:
        shutil.rmtree(directory)

    if totals.get_request_count() != 7:
        errmsg = f"Expected the retired worker's requests to stay counted, got {totals.get_request_count()}"
        raise AssertionError(errmsg)

    if totals.get_worker_statuses() != {2: "active"}:
        errmsg = f"Expected only the live worker's status, got {totals.get_worker_statuses()}"
        raise AssertionError(errmsg)

    if worker_file_left or retired["merged_pids"] != [1001]:
        errmsg = f"Expected the worker file folded into the retired file, got {worker_file_left} {retired['merged_pids']}"
        raise AssertionError(errmsg)

    return


def test_worker_file_not_yet_removed_is_counted_once():
    """
        A scrape between the retired file update and the removal of the
        worker file counts that worker once.
    """
    directory = tempfile.mkdtemp(prefix="metricsstore-")
    store = MetricsStore(directory, ServerConfig())

    try:
        store.write_snapshot(_collector_with(5, 1), pid=2001)
        snapshot_path = store.worker_file(2001)
        with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
            saved_snapshot = snapshot_file.read()

        store.retire_worker(2001)

        # The worker file as it was just before the master removed it
        with open(snapshot_path, "w", encoding="utf-8") as snapshot_file:
            snapshot_file.write(saved_snapshot)

        totals = store.collect()
    finally:
        shutil.rmtree(directory)

    if totals.get_request_count() != 5:
        errmsg = f"Expected the worker to be counted once, got {totals.get_request_count()}"
        raise AssertionError(errmsg)

    return


def test_retiring_a_worker_twice_or_without_snapshot_changes_nothing():
    """
        retire_worker is safe for a worker that wrote no snapshot or was retired.
    """
    directory = tempfile.mkdtemp(prefix="metricsstore-")
    store = MetricsStore(directory, ServerConfig())

    try:
        store.write_snapshot(_collector_with(2, 1), pid=3001)
        store.retire_worker(3001)
        store.retire_worker(3001)
        store.retire_worker(3002)
        totals = store.collect()
    finally:
        shutil.rmtree(directory)

    if totals.get_request_count() != 2:
        errmsg = f"Expected 2 requests, got {totals.get_request_count()}"
        raise AssertionError(errmsg)

    return


def test_snapshot_writer_keeps_the_snapshot_current():
    """
        The writer thread writes the counts of the worker without a scrape.
    """
    directory = tempfile.mkdtemp(prefix="metricsstore-")
    store = MetricsStore(directory, ServerConfig(), write_interval=0.05)
    collector = _collector_with(1, 1)

    try:
        store.start_snapshot_writer(collector)
        collector.record_request("/x", "GET", 200, 1.0)

        deadline = time.monotonic() + 5.0
        seen = 0
        while time.monotonic() < deadline:
            if os.path.exists(store.worker_file(os.getpid())):
                seen = store.collect().get_request_count()
                if seen == 2:
                    break
            time.sleep(0.02)

        store.stop_snapshot_writer()
        stopped = store._writer_thread is None
    finally:
        store.stop_snapshot_writer()
        shutil.rmtree(directory)

    if seen != 2 or not stopped:
        errmsg = f"Expected the writer to publish both requests and stop, saw {seen}, stopped={stopped}"
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
