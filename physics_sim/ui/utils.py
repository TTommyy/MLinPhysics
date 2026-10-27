"""Utility functions for UI components (framework independent)."""

import re
from numbers import Number

__all__: list[str] = [
    "format_number",
    "format_vector_for_display",
    "parse_vector_from_text",
    "format_numbers_in_text",
    "color_to_rgba",
    "sanitize_color",
    "get_display_size",
]

DECIMALS = 2

_NUMBER_RE = re.compile(r"(?<![\w.])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?(?![\w.])")


def format_number(value, decimals: int = DECIMALS) -> str:
    """Format a numeric value with fixed precision (default two decimals).

    Non numeric values are returned as ``str(value)``.
    """
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Number):
        try:
            return f"{float(value):.{decimals}f}"
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def format_vector_for_display(vector) -> str:
    """Format a vector as a string for display in input fields.

    Args:
        vector: List, tuple or numpy array of numbers

    Returns:
        Formatted string like "[1.00, 2.50]"
    """
    return "[" + ", ".join(format_number(x) for x in list(vector)) + "]"


def parse_vector_from_text(text: str) -> list[float]:
    """Parse a vector from text input.

    Args:
        text: String in format "[x, y]", "(x, y)" or "x, y"

    Returns:
        List of float values

    Raises:
        ValueError: If parsing fails
    """
    text = text.strip()
    if (text.startswith("[") and text.endswith("]")) or (
        text.startswith("(") and text.endswith(")")
    ):
        text = text[1:-1]
    if not text.strip():
        raise ValueError("empty vector")
    parts = [float(x.strip()) for x in text.split(",")]
    return parts


def format_numbers_in_text(text: str, decimals: int = DECIMALS) -> str:
    """Re-format every number found in a free text with fixed precision."""

    def _sub(match: re.Match) -> str:
        try:
            return f"{float(match.group(0)):.{decimals}f}"
        except ValueError:
            return match.group(0)

    return _NUMBER_RE.sub(_sub, str(text))


def sanitize_color(color, fallback=(128, 128, 128)) -> tuple[int, int, int]:
    """Clamp a color-like value to an RGB tuple of ints in 0..255."""
    try:
        vals = [float(c) for c in list(color)[:3]]
        if len(vals) < 3:
            raise ValueError
        return tuple(int(round(min(255.0, max(0.0, v)))) for v in vals)
    except (TypeError, ValueError):
        return tuple(fallback)


def color_to_rgba(color, alpha: float = 1.0) -> tuple[float, float, float, float]:
    """Convert a 0-255 RGB(A) color into a normalized RGBA tuple for Kivy."""
    if color is None:
        return (0.5, 0.5, 0.5, alpha)
    vals = list(color)
    r, g, b = sanitize_color(vals[:3])
    a = alpha
    if len(vals) >= 4:
        try:
            a = min(255.0, max(0.0, float(vals[3]))) / 255.0
        except (TypeError, ValueError):
            a = alpha
    return (r / 255.0, g / 255.0, b / 255.0, a)


def get_display_size(default: tuple[int, int] = (1600, 900)) -> tuple[int, int]:
    """Best effort detection of the primary display size in pixels."""
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        if width > 0 and height > 0:
            return int(width), int(height)
    except Exception:
        pass
    return default
