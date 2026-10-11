"""
PaperMC core downloader — fully async.
Uses Fill API v3: https://fill.papermc.io
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .utils import USER_AGENT, console, download_file

FILL_BASE = "https://fill.papermc.io/v3"


class PaperAPI:
    """Async client for PaperMC Fill API v3."""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> "PaperAPI":
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": USER_AGENT}
            )
        return self

    async def __aexit__(self, *exc) -> None:
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("PaperAPI must be used as async context manager")
        return self._session

    async def get_project(self, project: str = "paper") -> Dict[str, Any]:
        url = f"{FILL_BASE}/projects/{project}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def list_versions(self, project: str = "paper") -> List[str]:
        data = await self.get_project(project)
        versions: List[str] = []
        for group_versions in data.get("versions", {}).values():
            versions.extend(group_versions)

        def sort_key(v: str):
            parts = []
            for p in v.replace("-", ".").split("."):
                try:
                    parts.append(int(p))
                except ValueError:
                    parts.append(0)
            return tuple(parts)

        return sorted(set(versions), key=sort_key, reverse=True)

    async def get_builds(
        self, version: str, project: str = "paper"
    ) -> List[Dict[str, Any]]:
        url = f"{FILL_BASE}/projects/{project}/versions/{version}/builds"
        async with self.session.get(url) as resp:
            if resp.status == 404:
                raise ValueError(f"Version {version} not found for project {project}")
            resp.raise_for_status()
            return await resp.json()

    async def get_latest_stable_build(
        self, version: str, project: str = "paper"
    ) -> Dict[str, Any]:
        builds = await self.get_builds(version, project)
        stable = [b for b in builds if b.get("channel") == "STABLE"]
        if stable:
            return stable[0]
        if builds:
            console.print(
                f"[yellow]No STABLE build for {version}, using latest ({builds[0].get('channel')})[/]"
            )
            return builds[0]
        raise ValueError(f"No builds available for {version}")

    async def get_build(
        self, version: str, build_id: int | str, project: str = "paper"
    ) -> Dict[str, Any]:
        builds = await self.get_builds(version, project)
        if build_id == "latest":
            return builds[0] if builds else None
        for b in builds:
            if b.get("id") == int(build_id):
                return b
        raise ValueError(f"Build {build_id} not found for {version}")

    def _extract_download(self, build: Dict[str, Any]) -> Dict[str, Any]:
        downloads = build.get("downloads") or {}
        info = downloads.get("server:default") or downloads.get("application")
        if not info:
            raise ValueError("No server download found in build metadata")
        return info

    async def download_build(
        self,
        version: str,
        dest: Path,
        *,
        build_id: int | str = "latest",
        project: str = "paper",
        prefer_stable: bool = True,
    ) -> Path:
        if prefer_stable and build_id == "latest":
            build = await self.get_latest_stable_build(version, project)
        else:
            build = await self.get_build(version, build_id, project)

        info = self._extract_download(build)
        url = info["url"]
        name = info.get("name") or f"{project}-{version}-{build['id']}.jar"
        sha256 = (info.get("checksums") or {}).get("sha256")

        dest = Path(dest)
        if dest.is_dir():
            dest = dest / name

        console.print(
            f"[cyan]Downloading {project} {version} build {build['id']} "
            f"({build.get('channel', '?')})…[/]"
        )
        await download_file(
            self.session,
            url,
            dest,
            expected_sha256=sha256,
            description=f"{project} {version}#{build['id']}",
        )
        console.print(f"[green]✓[/] Saved → {dest}")
        return dest

    async def resolve_version(self, version: str | None, project: str = "paper") -> str:
        versions = await self.list_versions(project)
        if not versions:
            raise RuntimeError(f"No versions available for {project}")
        if version is None or version.lower() in ("latest", "newest"):
            return versions[0]
        if version not in versions:
            matches = [v for v in versions if v.startswith(version)]
            if matches:
                return matches[0]
            raise ValueError(
                f"Version '{version}' not found. Available: {', '.join(versions[:15])}…"
            )
        return version
