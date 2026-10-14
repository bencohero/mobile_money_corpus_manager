"""Shared write gate used by isolated backup validation.

The state file is deliberately small and contains no application data.  The
file lock makes the active-request counter safe across uvicorn worker
processes.  Production must not use this until the image containing this
module is deployed and the gate is placed in front of every write path.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path


class WriteFreezeError(RuntimeError):
    pass


def state_path() -> Path:
    return Path(os.getenv("WRITE_FREEZE_STATE_FILE", "/tmp/write-freeze/state.json"))


def lock_path() -> Path:
    return Path(os.getenv("WRITE_FREEZE_LOCK_FILE", str(state_path()) + ".lock"))


def initialized_path() -> Path:
    return state_path().with_name(state_path().name + ".initialized")


def _default() -> dict:
    return {"phase": "OPEN", "active_writes": 0, "epoch": 0}


def _normalise(value: object) -> dict:
    if not isinstance(value, dict):
        raise WriteFreezeError("invalid write-freeze state")
    phase = value.get("phase")
    active = value.get("active_writes")
    epoch = value.get("epoch")
    if (phase not in {"OPEN", "DRAINING", "FROZEN"}
            or type(active) is not int or active < 0
            or type(epoch) is not int or epoch < 0):
        raise WriteFreezeError("invalid write-freeze state")
    return {"phase": phase, "active_writes": active, "epoch": epoch}


def _read_unlocked() -> dict:
    path = state_path()
    try:
        value = _normalise(json.loads(path.read_text(encoding="utf-8")))
        _mark_initialized_unlocked()
        return value
    except FileNotFoundError:
        if initialized_path().exists():
            raise WriteFreezeError("write-freeze state is missing")
        try:
            value = _default()
            _write_unlocked(value)
            _mark_initialized_unlocked()
            return value
        except OSError as exc:
            raise WriteFreezeError("write-freeze state is not writable") from exc
    except (json.JSONDecodeError, OSError) as exc:
        raise WriteFreezeError("unreadable write-freeze state") from exc


def _mark_initialized_unlocked() -> None:
    marker = initialized_path()
    marker.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    try:
        os.write(fd, b"initialized\n")
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_unlocked(state: dict) -> None:
    path = state_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".state.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(state, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


@contextmanager
def locked_state():
    path = lock_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def status() -> dict:
    with locked_state():
        return _read_unlocked()


def enter_write() -> None:
    with locked_state():
        current = _read_unlocked()
        if current["phase"] != "OPEN":
            raise WriteFreezeError(current["phase"])
        current["active_writes"] += 1
        _write_unlocked(current)


def leave_write() -> None:
    with locked_state():
        current = _read_unlocked()
        current["active_writes"] = max(0, current["active_writes"] - 1)
        _write_unlocked(current)


def begin_drain() -> dict:
    with locked_state():
        current = _read_unlocked()
        if current["phase"] != "OPEN":
            raise WriteFreezeError(current["phase"])
        current["phase"] = "DRAINING"
        current["epoch"] += 1
        _write_unlocked(current)
        return current


def wait_frozen(timeout: float = 60.0, interval: float = 0.1) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with locked_state():
            current = _read_unlocked()
            if current["phase"] != "DRAINING":
                raise WriteFreezeError(current["phase"])
            if current["active_writes"] == 0:
                current["phase"] = "FROZEN"
                _write_unlocked(current)
                return current
        time.sleep(interval)
    raise TimeoutError("write drain did not reach zero before timeout")


def unfreeze() -> dict:
    with locked_state():
        current = _read_unlocked()
        if current["phase"] != "FROZEN" or current["active_writes"] != 0:
            raise WriteFreezeError(current["phase"])
        current["phase"] = "OPEN"
        _write_unlocked(current)
        return current


def is_mutating(scope: dict) -> bool:
    return scope.get("type") == "http" and scope.get("method", "GET").upper() in {"POST", "PUT", "PATCH", "DELETE"}


class WriteFreezeMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if not is_mutating(scope):
            await self.app(scope, receive, send)
            return
        try:
            enter_write()
        except WriteFreezeError:
            body = b'{"detail":"write maintenance in progress"}'
            await send({"type": "http.response.start", "status": 503,
                        "headers": [(b"content-type", b"application/json"),
                                    (b"content-length", str(len(body)).encode()),
                                    (b"retry-after", b"5")]})
            await send({"type": "http.response.body", "body": body})
            return
        try:
            await self.app(scope, receive, send)
        finally:
            leave_write()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Operate the shared write-freeze state")
    parser.add_argument("command", choices=("status", "drain", "freeze", "unfreeze", "check"))
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--phase", choices=("OPEN", "DRAINING", "FROZEN"))
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            result = status()
        elif args.command == "check":
            result = status()
            if (args.phase is not None and result["phase"] != args.phase) or result["active_writes"] != 0:
                print(json.dumps(result, sort_keys=True))
                return 2
        elif args.command == "drain":
            result = begin_drain()
        elif args.command == "freeze":
            current = status()
            if current["phase"] == "OPEN":
                begin_drain()
            elif current["phase"] == "FROZEN":
                result = current
                print(json.dumps(result, sort_keys=True))
                return 0
            result = wait_frozen(args.timeout)
        else:
            result = unfreeze()
    except Exception as exc:
        print(f"write-freeze failed: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
