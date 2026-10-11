"""Utility helpers for Sharp."""

from __future__ import annotations

import hashlib
import platform
import sys
from pathlib import Path
from typing import Optional

import aiofiles
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

console = Console()

# Shared UA for Paper / Adoptium; Modrinth uses its own stricter identity in modrinth.py
USER_AGENT = (
    "cizik5064-arch/Sharp/1.1.0 "
    "(Minecraft server tool; https://github.com/cizik5064-arch/Sharp)"
)


def get_os_arch() -> tuple[str, str]:
    """Return (os, arch) strings compatible with Adoptium / Paper APIs."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_map = {
        "linux": "linux",
        "darwin": "mac",
        "windows": "windows",
        "freebsd": "linux",  # best-effort for Temurin
    }
    os_name = os_map.get(system, system)

    arch_map = {
        "x86_64": "x64",
        "amd64": "x64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "armv7l": "arm",
        "armv6l": "arm",
        "i386": "x86",
        "i686": "x86",
        "ppc64le": "ppc64le",
        "s390x": "s390x",
        "riscv64": "riscv64",
    }
    arch = arch_map.get(machine, machine)
    return os_name, arch


def get_data_dir() -> Path:
    """Base directory for Sharp data (Java installs, servers, config)."""
    from platformdirs import user_data_dir

    path = Path(user_data_dir("sharp", "sharp-mc"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_java_dir() -> Path:
    path = get_data_dir() / "java"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_servers_dir() -> Path:
    path = get_data_dir() / "servers"
    path.mkdir(parents=True, exist_ok=True)
    return path


async def download_file(
    session,
    url: str,
    dest: Path,
    *,
    expected_sha256: Optional[str] = None,
    description: str = "Downloading",
) -> Path:
    """Download a file with progress bar and optional SHA-256 verification."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")

    headers = {"User-Agent": USER_AGENT}
    async with session.get(url, headers=headers, allow_redirects=True) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0)) or None

        sha = hashlib.sha256()
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(description, total=total)
            async with aiofiles.open(tmp, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 64):
                    await f.write(chunk)
                    sha.update(chunk)
                    progress.update(task, advance=len(chunk))

    digest = sha.hexdigest()
    if expected_sha256 and digest.lower() != expected_sha256.lower():
        tmp.unlink(missing_ok=True)
        raise ValueError(
            f"SHA-256 mismatch: expected {expected_sha256}, got {digest}"
        )

    tmp.replace(dest)
    return dest


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
