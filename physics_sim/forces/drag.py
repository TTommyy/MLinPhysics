#####
### Based on: https://en.wikipedia.org/wiki/Drag_(physics)#The_drag_equation
####

from typing import Any

import numpy as np

from physics_sim.core import Entity, Force, PhysicalEntity


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

    def apply_to(self, entity: Entity, dt: float) -> np.ndarray:
        """Calculate drag force based on velocity."""
        if not isinstance(entity, PhysicalEntity):
            return np.array([0.0, 0.0])

        velocity = entity.velocity
        if isinstance(velocity, np.ndarray):
            speed = np.linalg.norm(velocity)
        else:
            speed = velocity.magnitude()

        if speed < 0.001:  # Avoid division by zero
            return np.array([0.0, 0.0])

        # Get entity-specific properties
        drag_coef = entity.drag_coefficient  # C_D (0.47 for sphere)
        cross_section = entity.cross_sectional_area

        if self.linear:
            # Simplified linear drag: F = -k * v
            # Using C_D * A as combined coefficient
            k = drag_coef * cross_section
            if isinstance(velocity, np.ndarray):
                return velocity * (-k)
            else:
                v_array = np.array([velocity.x, velocity.y])
                return v_array * (-k)
        else:
            # Full quadratic drag equation: F = -(1/2) * ρ * v² * C_D * A * (v/|v|)
            # Direction: opposite to velocity (v/|v|)
            # Magnitude: (1/2) * ρ * v² * C_D * A
            drag_magnitude = (
                0.5 * self.fluid_density * (speed**2) * drag_coef * cross_section
            )
            if isinstance(velocity, np.ndarray):
                drag_direction = velocity / speed
            else:
                drag_direction = velocity.normalized()
                drag_direction = np.array([drag_direction.x, drag_direction.y])
            return drag_direction * (-drag_magnitude)

    def apply_to_batch(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        """Vectorized drag calculation for batch of entities.

        Args:
            velocities: Velocity vectors, shape (n, 2)
            kwargs: Must include 'drag_coeffs' and 'cross_sections' arrays

        Returns:
            Force vectors, shape (n, 2)
        """
        drag_coeffs = kwargs.get("drag_coeffs", np.ones(len(velocities)))
        cross_sections = kwargs.get("cross_sections", np.ones(len(velocities)))

        speeds = np.linalg.norm(velocities, axis=1, keepdims=True)

        # Avoid division by zero
        mask = speeds[:, 0] > 0.001
        result = np.zeros_like(velocities)

        if mask.sum() == 0:
            return result

        if self.linear:
            # Linear drag: F = -k * v
            k = drag_coeffs[mask] * cross_sections[mask]
            result[mask] = velocities[mask] * -k[:, np.newaxis]
        else:
            # Quadratic drag: F = -(1/2) * ρ * v² * C_D * A * (v/|v|)
            magnitude = (
                0.5
                * self.fluid_density
                * (speeds[mask] ** 2)
                * drag_coeffs[mask, np.newaxis]
                * cross_sections[mask, np.newaxis]
            )
            direction = velocities[mask] / speeds[mask]
            result[mask] = direction * -magnitude

        return result

    @classmethod
    def is_unique(cls) -> bool:
        """Only one drag force instance allowed."""
        return True

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        """Get default settable parameters for DragForce."""
        return {
            "fluid_density": {
                "type": "float",
                "default": 1.225,
                "min": 0.1,
                "max": 10.0,
                "label": "Fluid Density (kg/m³)",
            },
            "linear": {
                "type": "bool",
                "default": True,
                "label": "Linear Model",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        """Get metadata for editable parameters with current values."""
        return {
            "fluid_density": {
                "type": "float",
                "default": float(self.fluid_density),
                "min": 0.1,
                "max": 10.0,
                "label": "Fluid Density (kg/m³)",
            },
            "linear": {
                "type": "bool",
                "default": bool(self.linear),
                "label": "Linear Model",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        """Update drag parameters from config dict."""
        try:
            if "fluid_density" in config:
                self.fluid_density = float(config["fluid_density"])
            if "linear" in config:
                self.linear = bool(config["linear"])
            return True
        except (ValueError, TypeError):
            return False

    def __repr__(self) -> str:
        model = "linear" if self.linear else "quadratic"
        return f"DragForce(fluid_density={self.fluid_density}, model={model})"
