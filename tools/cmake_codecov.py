"""cmake_codecov.py"""

from asyncio import run
from os import environ
from sys import argv

from asyncio_cmd import main
from cmake_ninja import cmake
from ninja import ninja


async def cmake_codecov(*args: object) -> None:
    environ["CXXFLAGS"] = " ".join((
        "-Wall",
        "-Wpedantic",
        "-Werror",
        "-fcoverage-mapping",
        "-fprofile-instr-generate",
        "-mllvm",
        "-runtime-counter-relocation",
        environ.get("CXXFLAGS", ""),
    ))
    environ["LDFLAGS"] = " ".join(
        ("-Wno-unused-command-line-argument", environ.get("LDFLAGS", ""))
    )
    await cmake("build")
    await ninja("build", *args)


if __name__ == "__main__":
    with main():
        run(cmake_codecov(*argv[1:]))
