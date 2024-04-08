from asyncio import run
from asyncio.subprocess import PIPE
from re import compile
from sys import version_info

from asyncio_as_completed import as_completed
from asyncio_cmd import ci_args, cmd, main, splitlines
from g_ls_tree import g_ls_tree
from structlog import get_logger


async def lint(*args: object) -> bytes:
    return await cmd(*args, out=PIPE, log=False)


async def black(*files: object) -> bytes:
    if files:
        return await lint(
            "black",
            *ci_args("--check", "--diff"),
            "--enable-unstable-feature",
            "docstring_check_for_newline",
            "--enable-unstable-feature",
            "hex_codes_in_unicode_sequences",
            "--enable-unstable-feature",
            "hug_parens_with_braces_and_square_brackets",
            "--enable-unstable-feature",
            "is_simple_lookup_for_doublestar_expression",
            "--enable-unstable-feature",
            "multiline_string_handling",
            "--enable-unstable-feature",
            "no_normalize_fmt_skip_whitespace",
            "--enable-unstable-feature",
            "remove_redundant_guard_parens",
            "--enable-unstable-feature",
            "string_processing",
            "--enable-unstable-feature",
            "typed_params_trailing_comma",
            "--enable-unstable-feature",
            "unify_docstring_detection",
            "--enable-unstable-feature",
            "wrap_long_dict_values_in_parens",
            "--preview",
            "--target-version",
            f"py{version_info.major}{version_info.minor}",
            "--unstable",
            *files,
        )
    return b""


async def isort(*files: object) -> bytes:
    if files:
        return await lint(
            "isort",
            *ci_args("--check-only"),
            "--python-version",
            f"{version_info.major}{version_info.minor}",
            *files,
        )
    return b""


async def pylama(*files: object) -> bytes:
    if files:
        return await lint("pylama", "--linters", "mccabe,pycodestyle,pyflakes", *files)
    return b""


async def mypy(*files: object) -> bytes:
    if files:
        return await lint(
            "mypy",
            "--python-version",
            f"{version_info.major}.{version_info.minor}",
            "--warn-unused-configs",
            *files,
        )
    return b""


async def self_check() -> None:
    files = await g_ls_tree("py")
    files_mypy = await g_ls_tree("py", exclude=compile(r"stdlib/|.*/stdlib/"))
    {
        await get_logger().ainfo(line)
        for lines in await as_completed(
            iter((black(*files), isort(*files), pylama(*files), mypy(*files_mypy)))
        )
        for line in splitlines(lines)
    }


if __name__ == "__main__":
    with main():
        run(self_check())
