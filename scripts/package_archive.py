#!/usr/bin/env python3
from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path

FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def create_zip(source_dir: Path, output_zip: Path) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        output_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(item for item in source_dir.rglob("*") if item.is_file()):
            relative_path = path.relative_to(source_dir).as_posix()
            mode = path.stat().st_mode
            permissions = 0o755 if mode & 0o111 else 0o644

            info = zipfile.ZipInfo(relative_path, FIXED_TIMESTAMP)
            info.external_attr = (stat.S_IFREG | permissions) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            info._compresslevel = 9

            archive.writestr(info, path.read_bytes())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a deterministic zip archive for serverless deployment."
    )
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_zip", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    output_zip = args.output_zip.resolve()

    if not source_dir.is_dir():
        raise SystemExit(f"Source directory does not exist: {source_dir}")

    create_zip(source_dir, output_zip)


if __name__ == "__main__":
    main()
