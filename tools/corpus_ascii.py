"""corpus_ascii.py"""

from itertools import groupby
from pathlib import Path

from asyncio_cmd import main
from corpus_utils import bucket, gather_paths, is_ascii
from structlog import get_logger


def _is_ascii(path: Path) -> bool:
    return is_ascii(path.read_bytes())


if __name__ == "__main__":
    with main():
        paths = sorted(path for path in gather_paths() if _is_ascii(path))
        for file in paths:
            get_logger().info(file)
        for (name, contents), (_, corpus) in zip(
            groupby(paths, lambda file: bucket(file).name),
            groupby(sorted(gather_paths()), lambda file: bucket(file).name),
        ):
            total = len(list(corpus))
            ascii = len(list(contents))
            get_logger().info(
                f"{name}: {ascii} / {total} -> {ascii * 100 // total / 100}"
            )
