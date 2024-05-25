"""generate_utf8_id_continue.py."""

from pathlib import Path
from re import sub

from generate_utf8_utils import group_contiguous

utf8_id_continue = (
    Path(__file__).parent.parent / "library" / "grammar" / "utf8_id_continue.hpp"
).resolve()


def _a(end: int) -> str:
    id_start = {i for i in range(end) if chr(i).isidentifier()}
    id_start |= {
        i
        for i in range(end)
        if i not in id_start
        and all("".join((chr(j), chr(i))).isidentifier() for j in id_start)
    }
    return group_contiguous(sorted(id_start))


output = iter((_a(0x100), _a(0x110000)))

utf8_id_continue.write_text(
    sub(
        r"\bUtf8IdContinue\b[^;]+",
        lambda _: f"Utf8IdContinue = {next(output)}",
        utf8_id_continue.read_text(),
    )
)
