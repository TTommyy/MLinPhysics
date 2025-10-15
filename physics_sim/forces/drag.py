from physics_sim.core import Entity, Force, PhysicalEntity, Vector2D


class DragForce(Force):
    """Air resistance / drag force.

    F_drag = -k * v * |v|  (quadratic drag model)
    or F_drag = -k * v  (linear drag model)

    Applies to entities that have a drag_coefficient attribute.
    """

    def __init__(self, coefficient: float = 0.1, linear: bool = True):
        """
        Args:
            coefficient: Drag coefficient (higher = more drag)
            linear: If True, use linear drag model; if False, use quadratic
        """
        super().__init__("Drag")
        self.coefficient = coefficient
        self.linear = linear

    def should_apply_to(self, entity: Entity) -> bool:
        """Drag applies to all physical entities (they all have drag_coefficient property)."""
        return isinstance(entity, PhysicalEntity) and entity.drag_enabled

    def apply_to(self, entity: Entity, dt: float) -> Vector2D:
        """Calculate drag force based on velocity."""
        if not isinstance(entity, PhysicalEntity):
            return Vector2D(0, 0)

        # Get drag coefficient from entity property
        drag_coef = entity.drag_coefficient

        velocity = entity.velocity
        speed = velocity.magnitude()

        if speed < 0.001:  # Avoid division by zero
            return Vector2D(0, 0)

        if self.linear:
            # Linear drag: F = -k * v
            return velocity * (-drag_coef)
        else:
            # Quadratic drag: F = -k * v * |v|
            return velocity * (-drag_coef * speed)

    def __repr__(self) -> str:
        model = "linear" if self.linear else "quadratic"
        return f"DragForce(coefficient={self.coefficient}, model={model})"
