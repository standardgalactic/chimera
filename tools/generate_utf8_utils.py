"""generate_utf8_utils.py."""

from itertools import count, groupby
from typing import Iterable

from asyncio_cmd import chunks


def _group_bounds(t: Iterable[tuple[int, int]]) -> tuple[int, int]:
    groups = {e for e, _ in t}
    return (min(groups), max(groups))


def group_contiguous(t: Iterable[int]) -> str:
    return _ranges(
        i
        for _, group in groupby(zip(t, count()), lambda t: t[0] - t[1])
        for i in _group_bounds(group)
    )


def _ranges(it: Iterable[int]) -> str:
    return f"sor<tao::pegtl::utf8::ranges<{">,tao::pegtl::utf8::ranges<".join(
        ",".join(slc) for slc in chunks((hex(i) for i in it), 64)
    )}>>"
