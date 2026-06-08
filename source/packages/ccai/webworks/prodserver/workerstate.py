"""
    Worker state and status module for the production server.

    This module provides the WorkerState enum for worker lifecycle states
    and the WorkerStatus dataclass for reporting worker status information.
"""

from dataclasses import dataclass
from enum import Enum


class WorkerState(Enum):
    """
        Worker lifecycle states.

        Represents the possible states of a worker process during
        its lifecycle from idle through shutdown.
    """
    IDLE = "idle"
    ACTIVE = "active"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class WorkerStatus:
    """
        Status information for a worker process.

        Contains runtime information about a worker including its
        identity, process ID, current state, request count, memory
        usage, and uptime.
    """

    worker_id: int
    pid: int
    state: WorkerState
    request_count: int
    memory_usage: int
    uptime: float

    def as_dict(self):
        """
            Convert the worker status to a dictionary.

            :returns: Dictionary representation of the worker status.
        """
        rtnval = {
            "worker_id": self.worker_id,
            "pid": self.pid,
            "state": self.state.value,
            "request_count": self.request_count,
            "memory_usage": self.memory_usage,
            "uptime": self.uptime,
        }

        return rtnval
