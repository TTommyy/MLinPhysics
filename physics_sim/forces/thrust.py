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
        return isinstance(entity, PhysicalEntity) and entity.thrust_enabled

    def apply_to(self, entity: Entity, dt: float) -> Vector2D:
        """Apply thrust force if enabled."""
        if not isinstance(entity, PhysicalEntity):
            return Vector2D(0, 0)

        # Check if thrust is enabled and get thrust vector from entity properties
        if not entity.thrust_enabled:
            return Vector2D(0, 0)

        return entity.thrust_vector

    def __repr__(self) -> str:
        return "ThrustForce()"
