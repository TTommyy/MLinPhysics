"""Utility functions for UI components."""

__all__: list[str] = ["format_vector_for_display", "parse_vector_from_text"]


def format_vector_for_display(vector: list | tuple) -> str:
    """Format a vector as a string for display in input fields.

    Args:
        vector: List or tuple of numbers

    Returns:
        Formatted string like "[1.0, 2.5]"
    """
    formatted = []
    for x in vector:
        if isinstance(x, int):
            formatted.append(f"{x}")
        elif isinstance(x, float):
            formatted.append(f"{x:.2f}")
        else:
            formatted.append(str(x))
    return "[" + ", ".join(formatted) + "]"


def parse_vector_from_text(text: str) -> list[float]:
    """Parse a vector from text input.

    Args:
        text: String in format "[x, y]" or "x, y"

    Returns:
        List of float values

    Raises:
        ValueError: If parsing fails
    """
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = [float(x.strip()) for x in text.split(",")]
    return parts
