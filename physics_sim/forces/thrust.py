import numpy as np

from physics_sim.core import Entity, Force, PhysicalEntity


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

    def apply_to(self, entity: Entity, dt: float) -> np.ndarray:
        """Apply thrust force if enabled."""
        if not isinstance(entity, PhysicalEntity):
            return np.array([0.0, 0.0])

        # Check if thrust is enabled and get thrust vector from entity properties
        if not entity.thrust_enabled:
            return np.array([0.0, 0.0])

        thrust = entity.thrust_vector
        if isinstance(thrust, np.ndarray):
            return thrust
        else:
            return np.array([thrust.x, thrust.y])

    def __repr__(self) -> str:
        return "ThrustForce()"
