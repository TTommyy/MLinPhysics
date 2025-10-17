from typing import Any

from physics_sim.core import PhysicalEntity, Vector2D


class Ball(PhysicalEntity):
    """A spherical entity with physical properties.

    Represents a ball in the simulation with position, velocity,
    radius, mass, and visual properties.
    """

    def __init__(
        self,
        position: Vector2D,
        velocity: Vector2D,
        radius: float = 0.2,
        mass: float = 1.0,
        color: tuple[int, int, int] = (255, 0, 0),
        restitution: float = 1.0,
        drag_coefficient: float = 0.1,
        entity_id: str | None = None,
    ):
        """
        Args:
            position: Initial position vector
            velocity: Initial velocity vector
            radius: Ball radius in simulation units
            mass: Ball mass (affects physics interactions)
            color: RGB color tuple (0-255 each)
            restitution: Coefficient of restitution (bounciness, 0-1)
            entity_id: Optional unique identifier
        """
        super().__init__(position, velocity, mass, entity_id)
        self.radius = radius
        self.color = color
        self.restitution = restitution
        self._drag_coefficient = drag_coefficient
        self._drag_enabled = False
        self._acceleration = Vector2D(0, 0)

    @property
    def drag_enabled(self) -> bool:
        return self._drag_enabled

    @property
    def drag_coefficient(self) -> float:
        return self._drag_coefficient

    def apply_force(self, force: Vector2D):
        """Apply a force using F = ma."""
        self._acceleration = self._acceleration + (force / self.mass)

    def reset_acceleration(self):
        """Reset accumulated acceleration (called after integration)."""
        self._acceleration = Vector2D(0, 0)

    def get_acceleration(self) -> Vector2D:
        """Get current acceleration."""
        return self._acceleration

    def get_render_data(self) -> dict[str, Any]:
        """Return rendering information for this ball."""
        return {
            "type": "circle",
            "position": self.position.to_tuple(),
            "radius": self.radius,
            "color": self.color,
        }

    def get_physics_data(self) -> dict[str, Any]:
        """Get detailed physics data including ball-specific properties."""
        data = super().get_physics_data()
        data.update({
            "type": "Ball",
            "radius": self.radius,
            "acceleration": self._acceleration.to_tuple(),
            "acceleration_magnitude": self._acceleration.magnitude(),
            "restitution": self.restitution,
        })
        return data

    def get_config_data(self) -> dict[str, Any]:
        data = super().get_physics_data()
        data.update({
            "radius": self.radius,
            "acceleration": self._acceleration.to_tuple(),
            "acceleration_magnitude": self._acceleration.magnitude(),
            "restitution": self.restitution,
        })
        return data

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
            "velocity_x": {
                "type": "float",
                "default": self.velocity.x,
                "label": "Velocity X (m/s)",
            },
            "velocity_y": {
                "type": "float",
                "default": self.velocity.y,
                "label": "Velocity Y (m/s)",
            },
            "restitution": {
                "type": "float",
                "default": self.restitution,
                "min": 0.0,
                "max": 1.0,
                "label": "Restitution",
            },
            "drag_coefficient": {
                "type": "float",
                "default": self._drag_coefficient,
                "min": 0.0,
                "max": 5.0,
                "label": "Drag Coefficient",
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
            if "velocity_x" in config or "velocity_y" in config:
                vx = float(config.get("velocity_x", self.velocity.x))
                vy = float(config.get("velocity_y", self.velocity.y))
                self.velocity = Vector2D(vx, vy)
            if "restitution" in config:
                self.restitution = float(config["restitution"])
            if "drag_coefficient" in config:
                self._drag_coefficient = float(config["drag_coefficient"])
            if "color" in config:
                self.color = config["color"]
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def create_cannonball(
        cls,
        position: Vector2D | None = None,
        velocity: Vector2D | None = None,
    ) -> "Ball":
        """Factory method: Create a red cannonball with default properties."""
        return cls(
            position=position or Vector2D(0.2, 0.2),
            velocity=velocity or Vector2D(10.0, 10.0),
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
            position=Vector2D(
                random.uniform(0.5, width - 0.5),
                random.uniform(0.5, height - 0.5),
            ),
            velocity=Vector2D(
                random.uniform(-5, 5),
                random.uniform(-5, 5),
            ),
            radius=random.uniform(0.1, 0.3),
            mass=1.0,
            color=(
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255),
            ),
            restitution=random.uniform(0.7, 1.0),
        )
