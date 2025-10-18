import math
from typing import Any

import numpy as np

from physics_sim.core import PhysicalEntity


class Ball(PhysicalEntity):
    """A spherical entity with physical properties.

    Represents a ball in the simulation with position, velocity,
    radius, mass, and visual properties.
    """

    def __init__(
        self,
        position: np.ndarray,
        velocity: np.ndarray,
        radius: float = 0.5,
        mass: float = 1.0,
        color: tuple[int, int, int] = (255, 0, 0),
        restitution: float = 1.0,
        drag_coefficient: float = 0.47,
        entity_id: str | None = None,
    ):
        """
        Args:
            position: Initial position as np.ndarray([x, y]) or Vector2D (for compat)
            velocity: Initial velocity as np.ndarray([x, y]) or Vector2D (for compat)
            radius: Ball radius in simulation units
            mass: Ball mass (affects physics interactions)
            color: RGB color tuple (0-255 each)
            restitution: Coefficient of restitution (bounciness, 0-1)
            entity_id: Optional unique identifier
        """
        super().__init__(position, velocity, mass, entity_id)
        self._radius = radius
        self.color = color
        self.restitution = restitution
        self._drag_coefficient = drag_coefficient
        self._drag_enabled = True
        self._acceleration = np.array([0.0, 0.0])
        self._cross_sectional_area = self._calcualate_cross_sectional_area()

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float):
        self._radius = value
        self._cross_sectional_area = self._calcualate_cross_sectional_area()

    @property
    def drag_enabled(self) -> bool:
        return self._drag_enabled

    @property
    def drag_coefficient(self) -> float:
        return self._drag_coefficient

    @property
    def cross_sectional_area(self) -> float:
        return self._cross_sectional_area

    def apply_force(self, force: np.ndarray):
        """Apply a force using F = ma."""
        self._acceleration = self._acceleration + (force / self.mass)

    def reset_acceleration(self):
        """Reset accumulated acceleration (called after integration)."""
        self._acceleration = np.array([0.0, 0.0])

    def get_acceleration(self) -> np.ndarray:
        """Get current acceleration."""
        return self._acceleration

    def get_render_data(self) -> dict[str, Any]:
        """Return rendering information for this ball."""
        if isinstance(self.position, np.ndarray):
            position_tuple = tuple(self.position)
        else:
            position_tuple = self.position.to_tuple()

        return {
            "type": "circle",
            "position": position_tuple,
            "radius": self.radius,
            "color": self.color,
        }

    def get_physics_data(self) -> dict[str, Any]:
        """Get detailed physics data including ball-specific properties."""
        data = super().get_physics_data()

        if isinstance(self._acceleration, np.ndarray):
            acceleration_tuple = tuple(self._acceleration)
            acceleration_magnitude = float(np.linalg.norm(self._acceleration))
        else:
            acceleration_tuple = self._acceleration.to_tuple()
            acceleration_magnitude = self._acceleration.magnitude()

        data.update({
            "type": "Ball",
            "radius": self.radius,
            "acceleration": acceleration_tuple,
            "acceleration_magnitude": acceleration_magnitude,
            "restitution": self.restitution,
        })
        return data

    def get_config_data(self) -> dict[str, Any]:
        data = super().get_physics_data()

        if isinstance(self._acceleration, np.ndarray):
            acceleration_tuple = tuple(self._acceleration)
            acceleration_magnitude = float(np.linalg.norm(self._acceleration))
        else:
            acceleration_tuple = self._acceleration.to_tuple()
            acceleration_magnitude = self._acceleration.magnitude()

        data.update({
            "radius": self.radius,
            "acceleration": acceleration_tuple,
            "acceleration_magnitude": acceleration_magnitude,
            "restitution": self.restitution,
        })
        return data

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        """Get default settable parameters for Ball creation."""
        return {
            "radius": {
                "type": "float",
                "default": 0.5,
                "min": 0.1,
                "max": 2.0,
                "label": "Radius",
            },
            "mass": {
                "type": "float",
                "default": 1.0,
                "min": 0.1,
                "max": 100.0,
                "label": "Mass (kg)",
            },
            "velocity": {
                "type": "vector",
                "default": [0.0, 0.0],
                "label": "Velocity (m/s)",
            },
            "restitution": {
                "type": "float",
                "default": 1.0,
                "min": 0.0,
                "max": 1.0,
                "label": "Restitution",
            },
            "color": {
                "type": "color",
                "default": (255, 0, 0),
                "label": "Color",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all editable Ball parameters."""
        return {
            "radius": {
                "type": "float",
                "default": self.radius,
                "min": 0.1,
                "max": 2.0,
                "label": "Radius",
            },
            "mass": {
                "type": "float",
                "default": self.mass,
                "min": 0.1,
                "max": 100.0,
                "label": "Mass (kg)",
            },
            "velocity": {
                "type": "vector",
                "default": self.velocity.tolist(),
                "label": "Velocity (m/s)",
            },
            "restitution": {
                "type": "float",
                "default": self.restitution,
                "min": 0.0,
                "max": 1.0,
                "label": "Restitution",
            },
            "color": {
                "type": "color",
                "default": self.color,
                "label": "Color",
            },
        }

    def update_physics_data(self, config: dict[str, Any]) -> bool:
        """Update ball parameters from config dict."""
        try:
            if "radius" in config:
                self.radius = float(config["radius"])
            if "mass" in config:
                self.mass = float(config["mass"])
            if "velocity" in config:
                self.velocity = np.array(config["velocity"])
            if "restitution" in config:
                self.restitution = float(config["restitution"])
            if "color" in config:
                self.color = config["color"]
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def create_cannonball(
        cls,
        position: np.ndarray | None = None,
        velocity: np.ndarray | None = None,
    ) -> "Ball":
        """Factory method: Create a red cannonball with default properties."""
        return cls(
            position=position if position is not None else np.array([0.2, 0.2]),
            velocity=velocity if velocity is not None else np.array([10.0, 10.0]),
            radius=0.2,
            mass=1.0,
            color=(255, 0, 0),
            restitution=1.0,
        )

    @classmethod
    def create_random(cls, bounds: tuple[float, float]) -> "Ball":
        """Factory method: Create a ball with random properties."""
        import random

        width, height = bounds
        return cls(
            position=np.array([
                random.uniform(0.5, width - 0.5),
                random.uniform(0.5, height - 0.5),
            ]),
            velocity=np.array([
                random.uniform(-5, 5),
                random.uniform(-5, 5),
            ]),
            radius=random.uniform(0.1, 0.3),
            mass=1.0,
            color=(
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255),
            ),
            restitution=random.uniform(0.7, 1.0),
        )

    def _calcualate_cross_sectional_area(self):
        return math.pi * (self.radius**2)
