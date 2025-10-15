from physics_sim.core import Entity, Force, PhysicalEntity, Vector2D


class ThrustForce(Force):
    """Thrust force for rocket engines or similar propulsion.

    Entity-specific force that applies in a direction specified by the entity.
    Entities must have 'thrust_enabled' and 'thrust_vector' attributes.
    """

    def __init__(self):
        """Initialize thrust force."""
        super().__init__("Thrust")

    def should_apply_to(self, entity: Entity) -> bool:
        """Thrust applies to entities with thrust capability."""
        return (
            isinstance(entity, PhysicalEntity)
            and hasattr(entity, "thrust_enabled")
            and hasattr(entity, "thrust_vector")
        )

    def apply_to(self, entity: Entity, dt: float) -> Vector2D:
        """Apply thrust force if enabled."""
        if not isinstance(entity, PhysicalEntity):
            return Vector2D(0, 0)

        # Check if thrust is enabled
        if not getattr(entity, "thrust_enabled", False):
            return Vector2D(0, 0)

        # Get thrust vector from entity
        thrust_vector = getattr(entity, "thrust_vector", Vector2D(0, 0))

        return thrust_vector

    def __repr__(self) -> str:
        return "ThrustForce()"
