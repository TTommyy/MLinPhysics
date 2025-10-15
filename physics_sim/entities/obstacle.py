from typing import Any

from physics_sim.core import Entity, Vector2D


class RectangleObstacle(Entity):
    """A static rectangular obstacle.

    Represents an immovable rectangular object in the simulation.
    """

    def __init__(
        self,
        position: Vector2D,
        width: float,
        height: float,
        color: tuple[int, int, int] = (100, 100, 100),
        entity_id: str | None = None,
    ):
        """
        Args:
            position: Center position of the obstacle
            width: Width of the rectangle
            height: Height of the rectangle
            color: RGB color tuple (0-255 each)
            entity_id: Optional unique identifier
        """
        super().__init__(entity_id)
        self.position = position
        self.width = width
        self.height = height
        self.color = color
        self.static = True

    def get_render_data(self) -> dict[str, Any]:
        """Return rendering information for this obstacle."""
        return {
            "type": "rectangle",
            "position": self.position.to_tuple(),
            "width": self.width,
            "height": self.height,
            "color": self.color,
        }

    @classmethod
    def create_wall(
        cls,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> "RectangleObstacle":
        """Factory method: Create a wall obstacle.

        Args:
            x: X position (center)
            y: Y position (center)
            width: Wall width
            height: Wall height
        """
        return cls(
            position=Vector2D(x, y),
            width=width,
            height=height,
            color=(80, 80, 80),
        )


class CircleObstacle(Entity):
    """A static circular obstacle.

    Represents an immovable circular object in the simulation.
    """

    def __init__(
        self,
        position: Vector2D,
        radius: float,
        color: tuple[int, int, int] = (100, 100, 100),
        entity_id: str | None = None,
    ):
        """
        Args:
            position: Center position of the obstacle
            radius: Radius of the circle
            color: RGB color tuple (0-255 each)
            entity_id: Optional unique identifier
        """
        super().__init__(entity_id)
        self.position = position
        self.radius = radius
        self.color = color
        self.static = True

    def get_render_data(self) -> dict[str, Any]:
        """Return rendering information for this obstacle."""
        return {
            "type": "circle_static",
            "position": self.position.to_tuple(),
            "radius": self.radius,
            "color": self.color,
        }
