"""corpus_freeze.py"""

from asyncio import run
from asyncio.subprocess import PIPE
from base64 import b64encode
from json import dump, load
from lzma import compress
from os import environ
from pathlib import Path
from sys import argv

from asyncio_as_completed import as_completed
from asyncio_cmd import git_cmd, main
from corpus_ascii import is_ascii
from corpus_utils import c_tqdm, corpus_objects


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


async def corpus_freeze_main(output: str) -> None:
    await corpus_freeze(output, disable_bars=None)


if __name__ == "__main__":
    with main():
        run(corpus_freeze_main(*argv[1:]))
