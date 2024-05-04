"""corpus_freeze.py"""

from asyncio import run
from sys import argv

from asyncio_cmd import main
from corpus_utils import corpus_freeze


async def corpus_freeze_main(output: str) -> None:
    await corpus_freeze(output, disable_bars=None)


if __name__ == "__main__":
    with main():
        run(corpus_freeze_main(*argv[1:]))
