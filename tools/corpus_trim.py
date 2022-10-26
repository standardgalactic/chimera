# Copyright (c) 2022 Asa Katida <github@holomaplefeline.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""corpus_trim.py"""

from asyncio import as_completed, gather, run
from functools import cache
from hashlib import sha256
from itertools import chain
from os import chdir
from pathlib import Path
from re import MULTILINE, compile
from sys import stderr
from typing import Iterable, TypeVar

from asyncio_cmd import ProcessError, cmd
from asyncio_set_event_loop_policy import set_event_loop_policy
from tqdm import tqdm  # type: ignore

LENGTH = 22
DIRECTORIES = ("corpus", "crashes")
FUZZ = Path("unit_tests") / "fuzz"
CORPUS = FUZZ / "corpus"
CORPUS_ORIGINAL = FUZZ / "corpus_original"
CRASHES = FUZZ / "crashes"
T = TypeVar("T")
CONFLICT = compile(rb"^((<{8}|>{8})\s.+|={8})$\s", MULTILINE)


class Increment(Exception):
    pass


def c_tqdm(iterable: Iterable[T], desc: str) -> Iterable[T]:
    return tqdm(iterable, desc=desc, maxinterval=60, miniters=100, unit_scale=True)  # type: ignore


def conflicts_one(file: Path) -> None:
    set(
        map(
            lambda section: (file.parent / sha256(section).hexdigest()).write_bytes(
                section
            ),
            filter(None, CONFLICT.split(file.read_bytes())),
        )
    )
    file.unlink()


def conflicts(fuzz: Iterable[Path]) -> None:
    set(
        c_tqdm(
            map(
                conflicts_one,
                filter(
                    lambda file: CONFLICT.search(file.read_bytes()),
                    fuzz,
                ),
            ),
            "Conflicts",
        )
    )


def corpus_trim_one(fuzz: Iterable[Path]) -> None:
    global LENGTH
    for file in c_tqdm(fuzz, "Corpus rehash"):
        src_sha = sha(file)
        name = src_sha[:LENGTH]
        if any(
            map(
                lambda other: other.exists() and src_sha != sha(other),
                map(lambda directory: FUZZ / directory / name, DIRECTORIES),
            )
        ):
            LENGTH += 1
            raise Increment(
                f"Collision found, update corpus_trim.py `LENGTH`: {LENGTH}"
            )
        file.rename(file.parent / name)


def corpus_trim() -> None:
    while True:
        try:
            corpus_trim_one(gather_paths())
        except Increment:
            if LENGTH > 32:
                raise
            continue
        break


@cache
def fuzz_star() -> tuple[Path, ...]:
    return tuple(
        filter(
            lambda path: path.is_file() and path.stat().st_mode & 0o110,
            Path().rglob("fuzz-*"),
        )
    )


async def fuzz_test_one(regression: Path, *args: str, timeout: int) -> None:
    await cmd(
        str(regression),
        "-detect_leaks=0",
        "-use_value_profile=1",
        *args,
        timeout=timeout,
    )


async def fuzz_test(*args: str, timeout: int = 10) -> list[Exception]:
    return list(
        filter(
            None,
            await gather(
                *map(
                    lambda regression: fuzz_test_one(
                        regression, *args, timeout=timeout
                    ),
                    fuzz_star(),
                ),
                return_exceptions=True,
            ),
        )
    )


def gather_paths() -> Iterable[Path]:
    return chain.from_iterable(
        map(lambda directory: (FUZZ / directory).iterdir(), DIRECTORIES)
    )


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


async def regression_one(file: Path) -> None:
    if not await fuzz_test(str(file)):
        file.rename(CORPUS / file.name)


async def regression(fuzz: Iterable[Path]) -> None:
    errors: list[Exception] = []
    for coro in c_tqdm(as_completed(map(regression_one, fuzz)), "Regression"):
        try:
            await coro
        except Exception as error:
            errors.append(error)
    if errors:
        raise errors[0]


async def main() -> None:
    chdir(Path(__file__).parent.parent)
    if not fuzz_star():
        raise FileNotFoundError("No fuzz targets built")
    CORPUS.mkdir(exist_ok=True)
    CRASHES.mkdir(exist_ok=True)
    conflicts(gather_paths())
    corpus_trim()
    await regression(CRASHES.iterdir())
    for _ in range(2):
        CORPUS.mkdir(exist_ok=True)
        errors = await fuzz_test(
            "-merge=1",
            "-reduce_inputs=1",
            "-shrink=1",
            str(CORPUS),
            str(CORPUS_ORIGINAL),
            timeout=1200,
        )
        if not errors:
            break
    if errors:
        error = errors.pop()
        if errors:
            print("Extra Errors:", *errors, file=stderr, sep="\n")
        raise error
    for file in chain(
        Path().rglob("crash-*"), Path().rglob("leak-*"), Path().rglob("timeout-*")
    ):
        file.rename(CRASHES / sha(file))
    corpus_trim()


if __name__ == "__main__":
    try:
        set_event_loop_policy()
        run(main())
    except ProcessError as error:
        error.exit()
    except KeyboardInterrupt:
        print("KeyboardInterrupt", file=stderr)
