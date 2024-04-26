"""corpus_retest.py."""

from asyncio import run
from sys import argv

from asyncio_cmd import main
from cmake_codecov import cmake_codecov
from corpus_merge import corpus_merge
from corpus_utils import corpus_retest, corpus_trim, regression
from ninja import ninja


async def corpus_retest_main(build: str, ref: str = "") -> None:
    await cmake_codecov("fuzzers", "unit-test")
    await cmake_codecov("test")
    await corpus_retest()
    if ref == "refs/heads/stable":
        await ninja(build, "corpus")
    corpus_trim(disable_bars=None)
    if ref != "refs/heads/stable":
        await corpus_merge(disable_bars=None)
    await regression(build)


if __name__ == "__main__":
    with main():
        run(corpus_retest_main(*argv[1:]))
