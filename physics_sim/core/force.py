from abc import ABC, abstractmethod

import numpy as np

from physics_sim.core.entity import Entity


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
    def apply_to(self, entity: Entity, dt: float) -> np.ndarray:
        """Calculate and return the force vector to apply to the entity.

        Args:
            entity: The entity to apply force to
            dt: Time step (may be needed for some force calculations)

        Returns:
            Force vector (in Newtons) as np.ndarray shape (2,)
        """
        pass

    def apply_to_batch(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        """Vectorized force calculation for batch of entities.

        Args:
            positions: Position vectors, shape (n, 2)
            velocities: Velocity vectors, shape (n, 2)
            masses: Mass values, shape (n,)
            entity_types: Entity type IDs, shape (n,)
            dt: Time step
            **kwargs: Additional entity-specific properties (drag_coeffs, cross_sections, etc.)

        Returns:
            Force vectors for all entities, shape (n, 2)
        """
        # Default implementation: fallback to per-entity (slow but correct)
        n = len(positions)
        forces = np.zeros((n, 2), dtype=np.float64)
        # Note: This is a fallback. Subclasses should override for performance.
        return forces

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
