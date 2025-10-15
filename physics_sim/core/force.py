from abc import ABC, abstractmethod

from physics_sim.core.entity import Entity
from physics_sim.core.vector import Vector2D


class Force(ABC):
    """Abstract base class for forces in the simulation.

    Forces can be global (apply to all entities) or entity-specific
    (apply only to entities with certain properties).
    """

    def __init__(self, name: str):
        """
        Args:
            name: Human-readable name for this force (e.g., "Gravity", "Drag")
        """
        self.name = name

    @abstractmethod
    def should_apply_to(self, entity: Entity) -> bool:
        """Determine if this force should be applied to the given entity.

        Args:
            entity: The entity to check

        Returns:
            True if the force should be applied, False otherwise
        """
        pass

    @abstractmethod
    def apply_to(self, entity: Entity, dt: float) -> Vector2D:
        """Calculate and return the force vector to apply to the entity.

        Args:
            entity: The entity to apply force to
            dt: Time step (may be needed for some force calculations)

        Returns:
            Force vector (in Newtons)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
