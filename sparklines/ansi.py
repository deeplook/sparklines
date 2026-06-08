"""ANSI terminal output: block characters, colour, reverse-video downward bars."""

import os
from typing import Optional

try:
    import termcolor

    HAVE_TERMCOLOR = True
except ImportError:
    HAVE_TERMCOLOR = False

blocks = " ▁▂▃▄▅▆▇█"
# blocks[8-i]: upward char whose reverse-video produces a downward bar of height i/8.
_COMPLEMENT = [8 - i for i in range(9)]
# Top-fill Unicode fallback when ANSI is suppressed (NO_COLOR, TERM=dumb, …).
_INVERTED_UNICODE = " ▔▔▔▀▀▀▀█"


def _ansi_ok() -> bool:
    """Return True if emitting ANSI escape codes is appropriate.

    Respects NO_COLOR, ANSI_COLORS_DISABLED, and TERM=dumb, but does NOT
    require a TTY — inverted rendering is an explicit opt-in to ANSI output.
    """
    if os.environ.get("NO_COLOR") or os.environ.get("ANSI_COLORS_DISABLED"):
        return False
    return os.environ.get("TERM") != "dumb"


def _inverted_char(v: int, color: Optional[str] = None) -> str:
    """Return a character representing a downward bar of height v/8.

    When ANSI is available, uses the complement upward block character under
    reverse video, giving full 8-level resolution. Falls back to the closest
    top-fill Unicode character (▔/▀/█) when ANSI is suppressed by NO_COLOR,
    ANSI_COLORS_DISABLED, or TERM=dumb.
    """
    if v == 0:
        return " "
    if v == 8:
        if color and HAVE_TERMCOLOR and _ansi_ok():
            return termcolor.colored("█", color, force_color=True)
        return "█"
    if not _ansi_ok():
        return _INVERTED_UNICODE[v]
    ch = blocks[_COMPLEMENT[v]]
    if HAVE_TERMCOLOR:
        return termcolor.colored(ch, color, attrs=["reverse"], force_color=True)
    return f"\033[7m{ch}\033[27m"
