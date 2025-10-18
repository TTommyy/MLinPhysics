#####
### Based on: https://en.wikipedia.org/wiki/Drag_(physics)#The_drag_equation
####

from physics_sim.core import Entity, Force, PhysicalEntity, Vector2D


class DragForce(Force):
    """Air resistance / drag force.

    Drag force formula: `F_D = (1/2) * ρ * v^2 * C_D * A`
    Where:
    - `F_D` : Drag Force
    - `ρ` : density (Fluid density in kg/m³ (default: 1.225 for air at sea level))
    - `v` : speed
    - `C_D` : Drag Coefficient (Depended on given entity)
    - `A` : Cross Sectional Area
    """

    def __init__(self, fluid_density: float = 1.225, linear: bool = True):
        """
        Args:
            coefficient: Drag coefficient (higher = more drag)
            linear: If True, use linear drag model; if False, use quadratic
        """
        super().__init__("Drag")
        self.fluid_density = fluid_density
        self.linear = linear

    def should_apply_to(self, entity: Entity) -> bool:
        """Drag applies to all physical entities (they all have drag_coefficient property)."""
        return isinstance(entity, PhysicalEntity) and entity.drag_enabled

    def apply_to(self, entity: Entity, dt: float) -> Vector2D:
        """Calculate drag force based on velocity."""
        if not isinstance(entity, PhysicalEntity):
            return Vector2D(0, 0)

        velocity = entity.velocity
        speed = velocity.magnitude()

        if speed < 0.001:  # Avoid division by zero
            return Vector2D(0, 0)

        # Get entity-specific properties
        drag_coef = entity.drag_coefficient  # C_D (0.47 for sphere)
        cross_section = entity.cross_sectional_area

        if self.linear:
            # Simplified linear drag: F = -k * v
            # Using C_D * A as combined coefficient
            k = drag_coef * cross_section
            return velocity * (-k)
        else:
            # Full quadratic drag equation: F = -(1/2) * ρ * v² * C_D * A * (v/|v|)
            # Direction: opposite to velocity (v/|v|)
            # Magnitude: (1/2) * ρ * v² * C_D * A
            drag_magnitude = (
                0.5 * self.fluid_density * (speed**2) * drag_coef * cross_section
            )
            drag_direction = velocity.normalized()
            return drag_direction * (-drag_magnitude)

    def __repr__(self) -> str:
        model = "linear" if self.linear else "quadratic"
        return f"DragForce(coefficient={self.coefficient}, model={model})"
