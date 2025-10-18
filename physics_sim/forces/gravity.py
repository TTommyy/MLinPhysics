import numpy as np

from physics_sim.core import Entity, Force, PhysicalEntity


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

    def should_apply_to(self, entity: Entity) -> bool:
        """Gravity applies to all physical entities."""
        return isinstance(entity, PhysicalEntity)

    def apply_to(self, entity: Entity, dt: float) -> np.ndarray:
        """Calculate gravitational force: F = m * g."""
        if isinstance(entity, PhysicalEntity):
            return self.acceleration * entity.mass
        return np.array([0.0, 0.0])

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

    def __repr__(self) -> str:
        return f"LinearGravityForce(acceleration={self.acceleration})"
