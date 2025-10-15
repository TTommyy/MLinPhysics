from abc import ABC, abstractmethod
from typing import Any

from physics_sim.core.vector import Vector2D


class Entity(ABC):
    """Base class for all simulation entities."""

    def __init__(self, entity_id: str | None = None):
        self.id = entity_id or id(self).__str__()

    @abstractmethod
    def get_render_data(self) -> dict[str, Any]:
        """Return data needed for rendering this entity."""
        pass


class PhysicalEntity(Entity):
    """Base class for entities with physical properties."""

    def __init__(
        self,
        position: Vector2D,
        velocity: Vector2D,
        mass: float = 1.0,
        entity_id: str | None = None,
    ):
        super().__init__(entity_id)
        self.position = position
        self.velocity = velocity
        self.mass = mass
        self._applied_forces: list[
            tuple[str, Vector2D]
        ] = []  # (force_name, force_vector)

    @abstractmethod
    def apply_force(self, force: Vector2D):
        """Apply a force to this entity."""
        pass

    def track_force(self, force_name: str, force_vector: Vector2D):
        """Record a force application for data collection.

        Args:
            force_name: Name of the force (e.g., "Gravity", "Drag")
            force_vector: Force vector that was applied
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
            "position": self.position.to_tuple(),
            "velocity": self.velocity.to_tuple(),
            "speed": self.velocity.magnitude(),
            "applied_forces": [
                {"name": name, "vector": vec.to_tuple(), "magnitude": vec.magnitude()}
                for name, vec in self._applied_forces
            ],
        }
