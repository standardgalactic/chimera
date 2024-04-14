"""corpus_retest.py."""

from asyncio import run
from pathlib import Path
from sys import argv

from asyncio_cmd import main
from cmake_codecov import cmake_codecov
from corpus_utils import corpus_retest, corpus_trim, regression
from ninja import ninja

SOURCE = Path(__file__).parent.parent.resolve()
FUZZ = SOURCE / "unit_tests" / "fuzz"
CORPUS = FUZZ / "corpus"
CRASHES = FUZZ / "crashes"


async def corpus_retest_main(build: str, ref: str = "") -> None:
    await cmake_codecov("fuzzers", "unit-test")
    await cmake_codecov("test")
    await corpus_retest()
    await regression(build)
    if ref == "refs/heads/stable":
        await ninja(build, "corpus")
    corpus_trim(disable_bars=None)


if __name__ == "__main__":
    with main():
        run(corpus_retest_main(*argv[1:]))
