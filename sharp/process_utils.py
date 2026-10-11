"""
Cross-platform process helpers (Windows / macOS / Linux).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def process_alive(pid: int) -> bool:
    """Return True if process with given PID is still running."""
    if pid <= 0:
        return False
    if is_windows():
        try:
            os.kill(pid, 0)
            return True
        except (OSError, SystemError):
            try:
                out = subprocess.check_output(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                return str(pid) in out
            except (subprocess.CalledProcessError, FileNotFoundError, OSError):
                return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def terminate_process(pid: int, *, force: bool = False) -> bool:
    """
    Stop a process. Returns True if signal/command was sent successfully.
    On Windows: taskkill. On Unix: SIGTERM / SIGKILL.
    """
    if pid <= 0:
        return False
    try:
        if is_windows():
            args = ["taskkill", "/PID", str(pid)]
            if force:
                args.append("/F")
            args.append("/T")
            kwargs = {
                "stderr": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL,
            }
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            subprocess.run(args, check=False, **kwargs)
            return True
        else:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            return True
    except (OSError, ProcessLookupError):
        return False


def start_detached(
    cmd: Sequence[str],
    *,
    cwd: Path | str,
    log_file: Optional[Path] = None,
) -> int:
    """
    Start a process detached from the current session.
    Returns the PID of the new process.
    """
    cwd = str(cwd)
    stdout = subprocess.DEVNULL
    stderr = subprocess.DEVNULL
    log_handle = None

    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(log_file, "a", encoding="utf-8")  # noqa: SIM115
        stdout = log_handle
        stderr = subprocess.STDOUT

    try:
        if is_windows():
            flags = 0
            flags |= getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            proc = subprocess.Popen(
                list(cmd),
                cwd=cwd,
                stdout=stdout,
                stderr=stderr,
                creationflags=flags,
                close_fds=True,
            )
        else:
            proc = subprocess.Popen(
                list(cmd),
                cwd=cwd,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
                close_fds=True,
            )
        return proc.pid
    finally:
        if log_handle is not None:
            try:
                log_handle.close()
            except OSError:
                pass


def clear_screen() -> None:
    """Clear terminal (cross-platform)."""
    os.system("cls" if is_windows() else "clear")
