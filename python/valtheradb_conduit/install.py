from __future__ import annotations

import os
import platform
import stat
import subprocess
from pathlib import Path

DEFAULT_INSTALL_DIR = Path("./vendor/vdb")
DEFAULT_REPOSITORY = "wxn0brP/ValtheraDB-conduit"


def asset_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        arch = "arm64" if machine in ("aarch64", "arm64") else "x64"
        return f"valtheradb-conduit-linux-{arch}"
    if system == "darwin":
        arch = "arm64" if machine in ("aarch64", "arm64") else "x64"
        return f"valtheradb-conduit-darwin-{arch}"
    if system == "windows":
        return "valtheradb-conduit-windows-x64.exe"
    raise RuntimeError(f"unsupported platform: {system}/{machine}")


def binary_name() -> str:
    return "valtheradb-conduit.exe" if platform.system().lower() == "windows" else "valtheradb-conduit"


def binary_path(install_dir: str | os.PathLike[str] = DEFAULT_INSTALL_DIR) -> Path:
    return Path(install_dir) / binary_name()


def release_url(repository: str = DEFAULT_REPOSITORY, version: str | None = None) -> str:
    release = f"download/{version}" if version else "latest/download"
    return f"https://github.com/{repository}/releases/{release}/{asset_name()}"


def ensure_binary(
    install_dir: str | os.PathLike[str] = DEFAULT_INSTALL_DIR,
    *,
    auto_download: bool = False,
    repository: str = DEFAULT_REPOSITORY,
    version: str | None = None,
) -> Path:
    target = binary_path(install_dir)
    if target.exists():
        return target
    if not auto_download:
        raise FileNotFoundError(f"ValtheraDB Conduit binary not found: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".download")
    subprocess.run(["curl", "-fsSL", "-o", str(tmp), release_url(repository, version)], check=True)
    tmp.replace(target)

    if platform.system().lower() != "windows":
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--install-dir", default=str(DEFAULT_INSTALL_DIR))
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--version")
    args = parser.parse_args()
    print(ensure_binary(args.install_dir, auto_download=True, repository=args.repository, version=args.version))


if __name__ == "__main__":
    main()
