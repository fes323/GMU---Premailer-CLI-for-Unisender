"""Nonblocking OS lock; automatically released even if the process crashes."""
import os
from contextlib import contextmanager
from functools import wraps


@contextmanager
def project_lock():
    with open(".gmu.lock", "a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError("В этой папке уже выполняется команда GMU. Дождитесь её завершения.") from exc
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def locked_project(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        with project_lock():
            return function(*args, **kwargs)
    return wrapper
