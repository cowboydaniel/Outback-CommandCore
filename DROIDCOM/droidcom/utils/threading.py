"""Threading helpers that bridge Qt threading into legacy interfaces."""

import logging
import threading

from PySide6 import QtCore


class WorkerThread(QtCore.QThread):
    error = QtCore.Signal(str)

    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self._target = target
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            self._target(*self._args, **self._kwargs)
        except Exception as exc:
            self.error.emit(str(exc))


class QtThreadWrapper:
    def __init__(self, target=None, args=(), kwargs=None, daemon=None):
        self._worker = WorkerThread(target, *(args or ()), **(kwargs or {}))
        self.daemon = daemon
        self._worker.error.connect(lambda msg: logging.error(f"Worker thread error: {msg}"))

    def start(self):
        self._worker.start()

    def join(self, timeout=None):
        if timeout is None:
            self._worker.wait()
        else:
            self._worker.wait(int(timeout * 1000))

    def is_alive(self):
        return self._worker.isRunning()


threading.Thread = QtThreadWrapper
