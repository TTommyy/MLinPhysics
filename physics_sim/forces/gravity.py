from physics_sim.core import Entity, Force, PhysicalEntity, Vector2D


class GravityForce(Force):
    """Global gravitational force (F = m * g).

    Applies to all PhysicalEntity instances.
    """

    def __init__(self, acceleration: Vector2D):
        """
        Args:
            acceleration: Gravitational acceleration vector (e.g., Vector2D(0, -9.81))
        """
        super().__init__("Gravity")
        self.acceleration = acceleration

    def should_apply_to(self, entity: Entity) -> bool:
        """Gravity applies to all physical entities."""
        return isinstance(entity, PhysicalEntity)

    def apply_to(self, entity: Entity, dt: float) -> Vector2D:
        """Calculate gravitational force: F = m * g."""
        if isinstance(entity, PhysicalEntity):
            return self.acceleration * entity.mass
        return Vector2D(0, 0)

    def __repr__(self) -> str:
        return f"GravityForce(acceleration={self.acceleration})"
