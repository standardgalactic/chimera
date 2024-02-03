"""corpus_merge.py"""

from asyncio import run
from pathlib import Path
from sys import argv

from asyncio_cmd import main
from chimera_utils import rmdir
from cmake_codecov import cmake_codecov
from corpus_freeze import corpus_freeze
from corpus_utils import corpus_gather, corpus_trim, fuzz_test
from structlog import get_logger

SOURCE = Path(__file__).parent.parent.resolve()
FUZZ = SOURCE / "unit_tests" / "fuzz"
CORPUS = FUZZ / "corpus"
CORPUS_ORIGINAL = FUZZ / "corpus_original"


async def corpus_merge(disable_bars: bool | None) -> None:
    rmdir(CORPUS_ORIGINAL)
    CORPUS.rename(CORPUS_ORIGINAL)
    CORPUS.mkdir(exist_ok=True, parents=True)
    if errors := await fuzz_test(
        "-merge=1", "-reduce_inputs=1", "-shrink=1", CORPUS, *CORPUS_ORIGINAL.iterdir()
    ):
        error = errors.pop()
        for error in errors:
            await get_logger().aerror(f"Extra Error: {error}")
        raise error
    rmdir(CORPUS_ORIGINAL)
    corpus_trim(disable_bars=disable_bars)
    await corpus_freeze("unit_tests/fuzz/cases.json", disable_bars=None)


async def corpus_merge_main(base_reference: str = "HEAD") -> None:
    await cmake_codecov("fuzzers", "unit-test")
    await cmake_codecov("test")
    await corpus_gather(
        "unit_tests/fuzz/corpus", base_reference=base_reference, disable_bars=None
    )
    await corpus_merge(disable_bars=None)


if __name__ == "__main__":
    with main():
        run(corpus_merge_main(*argv[1:]))
