import numpy as np

from physics_sim.core import Entity, Force, PhysicalEntity


class EntitySpecificForce(Force):
    """Per-entity custom force that applies only to a specific entity.

    Allows applying custom forces (persistent or one-time) to individual entities
    during simulation. Forces are identified by entity ID.
    """

    def __init__(
        self, entity_id: str, name: str, force_vector: np.ndarray, enabled: bool = True
    ):
        """
        Args:
            entity_id: ID of the entity this force applies to
            name: Name of the force (e.g., "Custom Thrust", "Wind")
            force_vector: Force vector to apply (constant), np.ndarray shape (2,)
            enabled: Whether this force is currently active
        """
        super().__init__(name)
        self.entity_id = entity_id
        self.force_vector = force_vector
        self.enabled = enabled

    def should_apply_to(self, entity: Entity) -> bool:
        """Apply only to the specific target entity."""
        return (
            self.enabled
            and isinstance(entity, PhysicalEntity)
            and entity.id == self.entity_id
        )

    def apply_to(self, entity: Entity, dt: float) -> np.ndarray:
        """Return the constant force vector."""
        if self.should_apply_to(entity):
            return self.force_vector
        return np.array([0.0, 0.0])

    def set_force_vector(self, force_vector: np.ndarray):
        """Update the force vector dynamically."""
        self.force_vector = force_vector

    def toggle_enabled(self, enabled: bool | None = None):
        """Enable or disable this force."""
        if enabled is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enabled

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"EntitySpecificForce(entity_id={self.entity_id}, name={self.name}, status={status})"
