from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class Entity(ABC):
    """Base class for all simulation entities."""

    def __init__(self, entity_id: str | None = None):
        self.id = entity_id or id(self).__str__()

    @abstractmethod
    def get_render_data(self) -> dict[str, Any]:
        """Return data needed for rendering this entity."""
        pass

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        """Get default settable parameters for entity creation.

        Returns metadata for editable parameters (excludes position which is set by click).
        Subclasses should override this to provide their specific parameters.
        """
        return {}


class PhysicalEntity(Entity):
    """Base class for entities with physical properties."""

    def __init__(
        self,
        position: np.ndarray,
        velocity: np.ndarray,
        mass: float = 1.0,
        entity_id: str | None = None,
    ):
        super().__init__(entity_id)
        self.position = position
        self.velocity = velocity

        self.mass = mass
        self._applied_forces: list[
            tuple[str, np.ndarray]
        ] = []  # (force_name, force_vector)

    @abstractmethod
    def apply_force(self, force: np.ndarray):
        """Apply a force to this entity."""
        pass

    @property
    def drag_enabled(self) -> bool:
        """Whether drag force is currently enabled.

        Subclasses without drag force should override this property.
        Default is Ture.
        """
        True

    @property
    def drag_coefficient(self) -> float:
        """Coefficient of drag for air resistance calculations.

        Subclasses should override this property to provide entity-specific drag coefficients.
        """
        pass

    @property
    def cross_sectional_area() -> float:
        """Cross sectional area for drag fore calculation"""
        pass

    @property
    def thrust_enabled(self) -> bool:
        """Whether thrust/propulsion is currently enabled.

        Subclasses with thrust capability should override this property.
        Default is False (no thrust).
        """
        return False

    @property
    def thrust_vector(self) -> np.ndarray:
        """Current thrust force vector.

        Subclasses with thrust capability should override this property to return
        the current thrust direction and magnitude.
        Default is zero vector (no thrust).
        """
        return np.array([0.0, 0.0])

    def track_force(self, force_name: str, force_vector: np.ndarray):
        """Record a force application for data collection.

        Args:
            force_name: Name of the force (e.g., "Gravity", "Drag")
            force_vector: Force vector that was applied as np.ndarray
        """
        self._applied_forces.append((force_name, force_vector))

    def clear_force_tracking(self):
        """Clear tracked forces (called each frame)."""
        self._applied_forces.clear()

    def get_physics_data(self) -> dict[str, Any]:
        """Get detailed physics data for this entity.

        Returns:
            Dictionary containing mass, position, velocity, acceleration, and forces
        """
        return {
            "id": self.id,
            "mass": self.mass,
            "position": self.position,
            "velocity": self.velocity,
            "speed": float(np.linalg.norm(self.velocity)),
            "applied_forces": [
                {
                    "name": name,
                    "vector": tuple(vec),
                    "magnitude": float(np.linalg.norm(vec)),
                }
                for name, vec in self._applied_forces
            ],
        }

    @abstractmethod
    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all editable parameters.

        Returns:
            Dictionary mapping parameter names to their metadata:
            {
                "param_name": {
                    "type": "float" | "int" | "color" | "bool",
                    "default": default_value,
                    "min": min_value (optional),
                    "max": max_value (optional),
                    "label": "Display Label"
                }
            }
        """
        pass

    @abstractmethod
    def update_physics_data(self, config: dict[str, Any]) -> bool:
        """Update entity parameters from config dict.

        Args:
            config: Dictionary of parameter values to update

        Returns:
            True if update successful, False otherwise
        """
        pass
