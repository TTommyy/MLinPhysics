from typing import Any

import numpy as np

from physics_sim.core import Force


class LinearGravityForce(Force):
    """Global gravitational force (F = m * g).

    Applies to all PhysicalEntity instances.
    """

    def __init__(self, acceleration: np.ndarray | None = None):
        """
        Args:
            acceleration: Gravitational acceleration vector as np.ndarray([x, y])
                         Default: np.array([0, -9.81])
        """
        super().__init__("LinearGravityForce")
        self.acceleration = (
            acceleration if acceleration is not None else np.array([0.0, -9.81])
        )

    def apply_to_batch(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        """Vectorized gravity calculation: F = m * g for all entities.

        Args:
            masses: Mass values, shape (n,)
            (other args unused but required by interface)

        Returns:
            Force vectors, shape (n, 2)
        """
        # F = m * g, broadcast gravity vector to all masses
        # masses[:, np.newaxis] creates shape (n, 1) for broadcasting
        return self.acceleration * masses[:, np.newaxis]

    def get_potential_energy_contribution(
        self,
        positions: np.ndarray,
        masses: np.ndarray,
        **kwargs,
    ) -> float:
        """Calculate gravitational potential energy.

        PE = sum(m * g * h) where h is height from reference (y=0).
        For downward gravity (g_y < 0), higher positions have more PE.

        Args:
            positions: Position vectors, shape (n, 2)
            masses: Mass values, shape (n,)

        Returns:
            Total potential energy in Joules
        """
        # PE = m * g * h, where h is the y-coordinate (height)
        # acceleration is the gravity vector [g_x, g_y]
        # For standard gravity [0, -9.81], we get PE = -m * g_y * y
        # which gives positive PE for positive heights
        heights = positions[:, 1]  # y-coordinates
        g_magnitude = -self.acceleration[1]  # Negate to get positive for upward
        return float(np.sum(masses * g_magnitude * heights))

    @classmethod
    def is_unique(cls) -> bool:
        """Only one gravity force instance allowed."""
        return True

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        """Get default settable parameters for LinearGravityForce."""
        return {
            "acceleration": {
                "type": "vector",
                "default": [0.0, -9.81],
                "label": "acceleration [x, y]",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get metadata for editable parameters with current values."""
        return {
            "acceleration": {
                "type": "vector",
                "default": self.acceleration.tolist(),
                "label": "acceleration [x, y]",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        """Update gravity parameters from config dict."""
        try:
            if "acceleration" in config:
                self.acceleration = np.array(config["acceleration"])
            return True
        except (ValueError, TypeError, IndexError):
            return False

    def __repr__(self) -> str:
        return f"LinearGravityForce(acceleration={self.acceleration})"
