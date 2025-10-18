from typing import Any

import numpy as np

from physics_sim.core import Entity


class RectangleObstacle(Entity):
    """A static rectangular obstacle.

    Represents an immovable rectangular object in the simulation.
    """

    def __init__(
        self,
        position: np.ndarray | Any,
        width: float,
        height: float,
        color: tuple[int, int, int] = (100, 100, 100),
        entity_id: str | None = None,
    ):
        """
        Args:
            position: Center position as np.ndarray([x, y]) or Vector2D (for compat)
            width: Width of the rectangle
            height: Height of the rectangle
            color: RGB color tuple (0-255 each)
            entity_id: Optional unique identifier
        """
        super().__init__(entity_id)
        # Accept both numpy arrays and Vector2D for backward compatibility
        if hasattr(position, "x"):
            self.position = np.array([position.x, position.y])
        else:
            self.position = position
        self.width = width
        self.height = height
        self.color = color
        self.static = True

    def get_render_data(self) -> dict[str, Any]:
        """Return rendering information for this obstacle."""
        if isinstance(self.position, np.ndarray):
            position_tuple = tuple(self.position)
        else:
            position_tuple = self.position.to_tuple()

        return {
            "type": "rectangle",
            "position": position_tuple,
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
            position=np.array([x, y]),
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
        position: np.ndarray | Any,
        radius: float,
        color: tuple[int, int, int] = (100, 100, 100),
        entity_id: str | None = None,
    ):
        """
        Args:
            position: Center position as np.ndarray([x, y]) or Vector2D (for compat)
            radius: Radius of the circle
            color: RGB color tuple (0-255 each)
            entity_id: Optional unique identifier
        """
        super().__init__(entity_id)
        # Accept both numpy arrays and Vector2D for backward compatibility
        if hasattr(position, "x"):
            self.position = np.array([position.x, position.y])
        else:
            self.position = position
        self.radius = radius
        self.color = color
        self.static = True

    def get_render_data(self) -> dict[str, Any]:
        """Return rendering information for this obstacle."""
        if isinstance(self.position, np.ndarray):
            position_tuple = tuple(self.position)
        else:
            position_tuple = self.position.to_tuple()

        return {
            "type": "circle_static",
            "position": position_tuple,
            "radius": self.radius,
            "color": self.color,
        }
