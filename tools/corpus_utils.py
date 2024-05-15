"""corpus_utils.py"""

from asyncio.subprocess import PIPE
from base64 import b64encode
from functools import cache
from hashlib import sha256
from json import dump, load
from lzma import compress
from os import environ
from pathlib import Path
from re import MULTILINE, compile, escape, finditer
from string import printable
from typing import Iterable, Match, TypeVar

from asyncio_as_completed import as_completed
from asyncio_cmd import cmd_flog, git_cmd, splitlines
from chimera_utils import IN_CI
from crash_reset import crash_reset
from structlog import get_logger
from tqdm import tqdm

CONFLICT = compile(
    rb"^(?:<{7,8}(?:\s+HEAD:\S+)?|>{7,8}(?:\s+\w+\s+\([^\)]+\):\S+)?|={7,8}).*$\s?",
    MULTILINE,
)
DIRECTORIES = ("corpus", "crashes")
SOURCE = Path(__file__).parent.parent.resolve()
FUZZ = SOURCE / "unit_tests" / "fuzz"
CORPUS = FUZZ / "corpus"
CRASHES = FUZZ / "crashes"
LENGTH = 14

T = TypeVar("T")


class Increment(Exception):
    pass


def bucket(path: Path) -> Path:
    return FUZZ / path.relative_to(FUZZ).parts[0]


def c_tqdm(
    iterable: Iterable[T], desc: str, disable: bool | None, total: float | None = None
) -> Iterable[T]:
    if IN_CI and disable is not False:
        return iterable
    return tqdm(iterable, desc=desc, disable=disable, total=total, unit_scale=True)


async def commit_count(*paths: str, base_reference: str) -> int:
    return len(
        list(
            splitlines(
                await _commit_log_base(
                    *paths, args=("--oneline",), base_reference=base_reference
                )
            )
        )
    )


async def _commit_log_base(
    *paths: str, args: tuple[str, ...], base_reference: str
) -> bytes:
    return await git_cmd(
        "log",
        *("--all",) if base_reference.startswith("^") else (),
        "--break-rewrites=0",
        "--find-renames=100%",
        "--no-renames",
        *args,
        base_reference,
        "--",
        *paths,
        out=PIPE,
    )


async def commit_paths(
    *paths: str, base_reference: str, diff_filter: str
) -> Iterable[Match[bytes]]:
    return finditer(
        rb"commit:.+:(?P<sha>.+)(?P<paths>(?:\s+(?!commit:).+)+)",
        await _commit_log_base(
            *paths,
            args=(
                "--date=iso",
                "--name-only",
                "--pretty=format:commit:%cd:%h",
                diff_filter,
            ),
            base_reference=base_reference,
        ),
    )


def conflicts_one(file: Path) -> None:
    for section in CONFLICT.split(file.read_bytes()):
        if section:
            (file.parent / sha256(section).hexdigest()).write_bytes(section)
    file.unlink()


def conflicts(fuzz: Iterable[Path]) -> None:
    for file in (file for file in fuzz if CONFLICT.search(file.read_bytes())):
        conflicts_one(file)


async def corpus_cat(sha: str) -> tuple[str, bytes]:
    return (sha, await git_cmd("cat-file", "-p", sha, out=PIPE))


async def _corpus_creations(
    *paths: str, base_reference: str, disable_bars: bool | None
) -> Iterable[tuple[str, list[str]]]:
    return (
        (
            match["sha"].decode(),
            [
                line
                for line in splitlines(match["paths"])
                if any(line.startswith(path) for path in paths)
                and not Path(line).exists()
            ],
        )
        for match in c_tqdm(
            await commit_paths(
                *paths, base_reference=base_reference, diff_filter="--diff-filter=d"
            ),
            "Commits",
            disable_bars,
            total=await commit_count(*paths, base_reference=base_reference),
        )
    )


async def corpus_creations(
    *paths: str, base_reference: str, disable_bars: bool | None
) -> Iterable[tuple[str, list[str]]]:
    return (
        (sha, files)
        for sha, files in await _corpus_creations(
            *paths, base_reference=base_reference, disable_bars=disable_bars
        )
        if files
    )


async def corpus_creations_new(
    *paths: str, disable_bars: bool | None
) -> Iterable[tuple[str, list[str]]]:
    exclude = frozenset(
        splitlines(
            await git_cmd(
                "log",
                "--break-rewrites=0",
                "--diff-filter=d",
                "--find-renames=100%",
                "--name-only",
                "--no-renames",
                "--pretty=format:",
                "origin/stable",
                "--",
                *paths,
                out=PIPE,
            )
        )
    ).union(map(str, gather_paths()))
    return (
        (sha, files)
        for sha, files in (
            (sha, sorted(frozenset(files) - exclude))
            for sha, files in await _corpus_creations(
                *paths, base_reference="^origin/stable", disable_bars=disable_bars
            )
        )
        if files
    )


async def corpus_deletions(
    *paths: str, base_reference: str, disable_bars: bool | None
) -> Iterable[str]:
    return (
        line
        for match in c_tqdm(
            await commit_paths(
                *paths, base_reference=base_reference, diff_filter="--diff-filter=D"
            ),
            "Commits",
            disable_bars,
            total=await commit_count(*paths, base_reference=base_reference),
        )
        for line in splitlines(match["paths"])
        if any(line.startswith(path) for path in paths) and Path(line).exists()
    )


async def corpus_freeze(
    output: str,
    *,
    base_reference: str = environ.get("BASE_REF", "HEAD"),
    disable_bars: bool | None,
) -> None:
    file = Path(output)
    with file.open() as istream:
        cases = {key: value for key, value in load(istream).items()}
    seen = Path("build/seen.json")
    if seen.exists():
        with seen.open() as istream:
            seen_existing = {key for key in load(istream)}
    else:
        seen_existing = set()
    crashes = [
        path for path in Path("unit_tests/fuzz/crashes").rglob("*") if path.is_file()
    ]
    existing = (
        frozenset(
            key.strip().decode()
            for key in await as_completed(
                c_tqdm(
                    (git_cmd("hash-object", path, out=PIPE) for path in crashes),
                    "Hash corpus",
                    disable_bars,
                    total=len(crashes),
                )
            )
        )
        | seen_existing
    )
    for key in existing.intersection(cases.keys()):
        del cases[key]
    all_cases = {
        sha: obj
        for sha, obj in await corpus_objects(
            "unit_tests/fuzz/corpus",
            "unit_tests/fuzz/crashes",
            base_reference=base_reference,
            disable_bars=disable_bars,
            exclude=existing.union(cases.keys()),
        )
    }
    seen_existing.update(all_cases.keys())
    cases.update(
        (sha, b64encode(compress(obj)).decode())
        for sha, obj in all_cases.items()
        if is_ascii(obj) and obj.decode().isprintable()
    )
    with file.open("w") as ostream:
        dump(cases, ostream, indent=4, sort_keys=True)
    seen.parent.mkdir(parents=True, exist_ok=True)
    with seen.open("w") as ostream:
        dump(list(seen_existing), ostream, indent=4, sort_keys=True)


async def corpus_gather(
    *paths: str,
    base_reference: str = environ.get("BASE_REF", "HEAD"),
    disable_bars: bool | None,
) -> None:
    exclude = frozenset(
        line.strip().decode()
        for line in await as_completed(
            c_tqdm(
                (git_cmd("hash-object", case, out=PIPE) for case in gather_paths()),
                "Gather existing corpus objects",
                disable_bars,
                total=len(list(gather_paths())),
            )
        )
    )
    for path in paths:
        Path(path).mkdir(exist_ok=True, parents=True)
        for sha, case in await corpus_objects(
            path,
            base_reference=base_reference,
            disable_bars=disable_bars,
            exclude=exclude,
        ):
            new_file = Path(path) / sha
            new_file.write_bytes(case)
        for sha, case in await corpus_objects_new(path, disable_bars=disable_bars):
            new_file = Path(path) / sha
            new_file.write_bytes(case)
    for path in await corpus_deletions(
        *paths, base_reference=base_reference, disable_bars=disable_bars
    ):
        Path(path).unlink()
    corpus_trim(disable_bars=disable_bars)


async def corpus_gather_new(*paths: str, disable_bars: bool | None) -> None:
    for path in paths:
        Path(path).mkdir(exist_ok=True, parents=True)
        for sha, case in await corpus_objects_new(path, disable_bars=disable_bars):
            new_file = Path(path) / sha
            new_file.write_bytes(case)
    corpus_trim(disable_bars=disable_bars)


async def corpus_objects(
    *paths: str,
    base_reference: str,
    disable_bars: bool | None,
    exclude: frozenset[str] = frozenset(),
) -> list[tuple[str, bytes]]:
    return await as_completed(
        corpus_cat(sha)
        for sha in c_tqdm(
            frozenset(
                line
                for lines in await as_completed(
                    git_cmd(
                        "ls-tree",
                        "--full-tree",
                        "--object-only",
                        "-r",
                        commit,
                        *paths,
                        out=PIPE,
                    )
                    for commit, _ in await corpus_creations(
                        *paths, base_reference=base_reference, disable_bars=disable_bars
                    )
                )
                for line in splitlines(lines)
            )
            - exclude,
            "Files",
            disable_bars,
        )
    )


async def corpus_objects_new(
    *paths: str, disable_bars: bool | None
) -> list[tuple[str, bytes]]:
    return await as_completed(
        corpus_cat(sha)
        for sha in c_tqdm(
            frozenset(
                line
                for lines in await as_completed(
                    git_cmd(
                        "ls-tree",
                        "--full-tree",
                        "--object-only",
                        "-r",
                        commit,
                        *paths,
                        out=PIPE,
                    )
                    for commit, _ in await corpus_creations_new(
                        *paths, disable_bars=disable_bars
                    )
                )
                for line in splitlines(lines)
            ),
            "Files",
            disable_bars,
        )
    )


async def corpus_retest() -> None:
    await corpus_gather_new(
        "unit_tests/fuzz/crashes", "unit_tests/fuzz/corpus", disable_bars=None
    )
    crash_reset()
    while await regression_log():
        await get_logger().ainfo(
            "Regression failed, retrying with"
            f" {sum(len(list(path.iterdir())) for path in CORPUS.iterdir())} cases"
        )
    for done in CORPUS.rglob(".done"):
        done.unlink()


def corpus_trim_one(fuzz: Iterable[Path], disable_bars: bool | None) -> None:
    global LENGTH
    for file in c_tqdm(fuzz, "Corpus rehash", disable_bars):
        src_sha = sha(file)
        name = src_sha[:LENGTH]
        if name == (file.parent.name + file.name):
            continue
        sha_bucket, name = name[:2], name[2:]
        if frozenset(
            sha(path)
            for path in (
                FUZZ / directory / sha_bucket / name for directory in DIRECTORIES
            )
            if path.exists()
        ).difference((src_sha,)):
            raise Increment(
                f"Collision found, update corpus_trim.py `LENGTH`: {LENGTH}"
            )
        new_file = bucket(file) / sha_bucket / name
        new_file.parent.mkdir(exist_ok=True, parents=True)
        file.rename(new_file)
    for file in (
        CORPUS / path.relative_to(bucket(path))
        for path in CRASHES.rglob("*")
        if path.is_file()
    ):
        file.unlink(missing_ok=True)


def corpus_trim(disable_bars: bool | None) -> None:
    global LENGTH
    conflicts(gather_paths())
    CRASHES.mkdir(exist_ok=True, parents=True)
    for file in (
        file
        for crash in ("crash-*", "leak-*", "timeout-*")
        for file in SOURCE.rglob(crash)
        if file.is_file() and ".git" not in file.parts
    ):
        file.rename(CRASHES / sha(file))
    while True:
        try:
            corpus_trim_one(gather_paths(), disable_bars)
        except Increment:
            if LENGTH > 32:
                raise
            LENGTH += 1
            continue
        break


def fuzz_output_paths(prefix: bytes, output: bytes) -> frozenset[bytes]:
    return frozenset(
        m["path"] for m in finditer(escape(prefix) + rb"\s+(?P<path>\S+)", output)
    )


@cache
def fuzz_star(build: Path = SOURCE) -> list[Path]:
    return [
        path
        for path in build.rglob("fuzz-*")
        if path.is_file() and path.stat().st_mode & 0o110
    ]


def gather_paths() -> Iterable[Path]:
    return (
        path
        for directory in DIRECTORIES
        for path in (FUZZ / directory).rglob("*")
        if path.is_file()
    )


def is_ascii(data: bytes) -> bool:
    try:
        return all(c in printable for c in data.decode())
    except UnicodeDecodeError:
        return False


async def regression(build: str, fuzzer: str = "") -> None:
    fuzzers = (Path(build) / f"fuzz-{fuzzer}",) if fuzzer else fuzz_star(Path(build))
    await as_completed(
        cmd_flog(fuzz, *args)
        for args in (
            sorted(path for path in corpus.iterdir() if path.name != ".done")
            for corpus in CORPUS.iterdir()
        )
        for fuzz in fuzzers
        if args
    )


async def regression_log() -> list[Exception]:
    return [
        exc
        for exc in await as_completed(
            regression_log_one(fuzz, *args)
            for args in (
                sorted(path for path in corpus.iterdir())
                for corpus in CORPUS.iterdir()
                if not (corpus / ".done").exists()
            )
            for fuzz in fuzz_star()
            if args
        )
        if exc is not None
    ]


async def regression_log_one(fuzzer: Path, *chunk: Path) -> Exception | None:
    log_file = Path("/tmp") / f"{fuzzer.name}-{chunk[0].parent.name}.log"
    log_file.write_bytes(b"")
    try:
        await cmd_flog(fuzzer, *chunk, out=log_file)
    except Exception as err:
        return err
    finally:
        log_output = log_file.read_bytes()
        for file in (
            Path(path.decode())
            for path in fuzz_output_paths(b"Running:", log_output)
            - fuzz_output_paths(b"Executed", log_output)
        ):
            try:
                file.rename(CRASHES / (file.parent.name + file.name))
            except FileNotFoundError:
                pass
        log_file.unlink(missing_ok=True)
    (chunk[0].parent / ".done").touch()
    return None


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
