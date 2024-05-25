"""generate_utf8_id_insane.py."""

from pathlib import Path
from re import sub

from generate_utf8_utils import _ranges

utf8_id_insane = (
    Path(__file__).parent.parent / "library" / "grammar" / "utf8_id_insane.hpp"
).resolve()

id_start = {i for i in range(0x110000) if chr(i).isidentifier()}

output = _ranges(
    next(
        s
        for s in ("".join((chr(s), chr(i))) for s in id_start for i in range(0x110000))
        if s.isidentifier()
    ).encode()
)

utf8_id_insane.write_text(
    sub(
        r"\bUtf8IdContinue\b[^;]+",
        f"Utf8IdContinue = {output}",
        utf8_id_insane.read_text(),
    )
)
