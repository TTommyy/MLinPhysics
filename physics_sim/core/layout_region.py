from dataclasses import dataclass

__all__: list[str] = ["LayoutRegion"]


@dataclass
class LayoutRegion:
    """Defines a rectangular region in screen space."""

    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        """Right edge X coordinate."""
        return self.x + self.width

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        """Top edge Y coordinate."""
        return self.y + self.height

    @property
    def bottom(self) -> int:
        return self.y

    @property
    def center_x(self) -> int:
        """Center X coordinate."""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """Center Y coordinate."""
        return self.y + self.height // 2
