"""generate_utf8_space.py."""

from pathlib import Path
from re import sub

from generate_utf8_utils import group_contiguous

utf8_space = (
    Path(__file__).parent.parent / "library" / "grammar" / "utf8_space.hpp"
).resolve()

output = iter((
    group_contiguous(i for i in range(0x100) if chr(i).isspace()),
    group_contiguous(i for i in range(0x110000) if chr(i).isspace()),
))

utf8_space.write_text(
    sub(
        r"\bUtf8Space\b[^;]+",
        lambda _: f"Utf8Space = {next(output)}",
        utf8_space.read_text(),
    )
)
