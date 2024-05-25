"""generate_utf8_id_start.py."""

from pathlib import Path
from re import sub

from generate_utf8_utils import group_contiguous

utf8_id_start = (
    Path(__file__).parent.parent / "library" / "grammar" / "utf8_id_start.hpp"
).resolve()

output = iter((
    group_contiguous(i for i in range(0x100) if chr(i).isidentifier()),
    group_contiguous(i for i in range(0x110000) if chr(i).isidentifier()),
))

utf8_id_start.write_text(
    sub(
        r"\bUtf8IdStart\b[^;]+",
        lambda _: f"Utf8IdStart = {next(output)}",
        utf8_id_start.read_text(),
    )
)
