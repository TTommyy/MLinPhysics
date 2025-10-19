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
        friction_coefficient: float = 0.2,
    ):
        """
        Args:
            position: Center position as np.ndarray([x, y])
            width: Width of the rectangle
            height: Height of the rectangle
            color: RGB color tuple (0-255 each)
            entity_id: Optional unique identifier
            friction_coefficient: Coefficient of friction for collisions
        """
        super().__init__(entity_id)

        self.position = position
        self.width = width
        self.height = height
        self.color = color
        self.static = True
        self._friction_coefficient = friction_coefficient

    @property
    def friction_coefficient(self) -> float:
        return self._friction_coefficient

    @friction_coefficient.setter
    def friction_coefficient(self, value: float):
        self._friction_coefficient = value

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        """Get default settable parameters for RectangleObstacle creation."""
        return {
            "width": {
                "type": "float",
                "default": 2.0,
                "min": 0.1,
                "max": 10.0,
                "label": "Width",
            },
            "height": {
                "type": "float",
                "default": 0.3,
                "min": 0.1,
                "max": 10.0,
                "label": "Height",
            },
            "color": {
                "type": "color",
                "default": (100, 100, 100),
                "label": "Color",
            },
            "friction_coefficient": {
                "type": "float",
                "default": 0.2,
                "min": 0.0,
                "max": 1.0,
                "label": "Friction Coefficient",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all editable RectangleObstacle parameters."""
        return {
            "width": {
                "type": "float",
                "default": self.width,
                "min": 0.1,
                "max": 10.0,
                "label": "Width",
            },
            "height": {
                "type": "float",
                "default": self.height,
                "min": 0.1,
                "max": 10.0,
                "label": "Height",
            },
            "color": {
                "type": "color",
                "default": self.color,
                "label": "Color",
            },
            "friction_coefficient": {
                "type": "float",
                "default": self.friction_coefficient,
                "min": 0.0,
                "max": 1.0,
                "label": "Friction Coefficient",
            },
        }

    def update_physics_data(self, config: dict[str, Any]) -> bool:
        """Update obstacle parameters from config dict."""
        try:
            if "width" in config:
                self.width = float(config["width"])
            if "height" in config:
                self.height = float(config["height"])
            if "color" in config:
                self.color = config["color"]
            if "friction_coefficient" in config:
                self.friction_coefficient = float(config["friction_coefficient"])
            return True
        except (ValueError, TypeError):
            return False

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
        friction_coefficient: float = 0.2,
    ):
        """
        Args:
            position: Center position as np.ndarray([x, y])
            radius: Radius of the circle
            color: RGB color tuple (0-255 each)
            entity_id: Optional unique identifier
            friction_coefficient: Coefficient of friction for collisions
        """
        super().__init__(entity_id)
        self.position = position
        self.radius = radius
        self.color = color
        self.static = True
        self._friction_coefficient = friction_coefficient

    @property
    def friction_coefficient(self) -> float:
        return self._friction_coefficient

    @friction_coefficient.setter
    def friction_coefficient(self, value: float):
        self._friction_coefficient = value

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        """Get default settable parameters for CircleObstacle creation."""
        return {
            "radius": {
                "type": "float",
                "default": 1.0,
                "min": 0.1,
                "max": 5.0,
                "label": "Radius",
            },
            "color": {
                "type": "color",
                "default": (100, 100, 100),
                "label": "Color",
            },
            "friction_coefficient": {
                "type": "float",
                "default": 0.2,
                "min": 0.0,
                "max": 1.0,
                "label": "Friction Coefficient",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all editable CircleObstacle parameters."""
        return {
            "radius": {
                "type": "float",
                "default": self.radius,
                "min": 0.1,
                "max": 5.0,
                "label": "Radius",
            },
            "color": {
                "type": "color",
                "default": self.color,
                "label": "Color",
            },
            "friction_coefficient": {
                "type": "float",
                "default": self.friction_coefficient,
                "min": 0.0,
                "max": 1.0,
                "label": "Friction Coefficient",
            },
        }

    def update_physics_data(self, config: dict[str, Any]) -> bool:
        """Update obstacle parameters from config dict."""
        try:
            if "radius" in config:
                self.radius = float(config["radius"])
            if "color" in config:
                self.color = config["color"]
            if "friction_coefficient" in config:
                self.friction_coefficient = float(config["friction_coefficient"])
            return True
        except (ValueError, TypeError):
            return False
