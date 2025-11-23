from typing import Any

import numpy as np
from numba import njit

from physics_sim.core import Force


@njit
def _compute_linear_gravity_force(
    masses: np.ndarray,
    acceleration: np.ndarray,
) -> np.ndarray:
    """JIT-compiled kernel for linear gravity calculation."""
    return acceleration * masses[:, np.newaxis]


@njit
def _compute_linear_gravity_potential_energy(
    positions: np.ndarray,
    masses: np.ndarray,
    g_magnitude: float,
) -> float:
    """JIT-compiled kernel for potential energy calculation."""
    heights = positions[:, 1]
    return float(np.sum(masses * g_magnitude * heights))


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
        self.g_magnitude = -self.acceleration[1]

    @classmethod
    def get_name(cls) -> str:
        return "LinearGravityForce"

    def apply_force(
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
        return _compute_linear_gravity_force(masses, self.acceleration)

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
        return _compute_linear_gravity_potential_energy(
            positions=positions, masses=masses, g_magnitude=self.g_magnitude
        )

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

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        return {}
