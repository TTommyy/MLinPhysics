#####
### Based on: https://en.wikipedia.org/wiki/Drag_(physics)#The_drag_equation
####

from __future__ import annotations

from typing import Any

import numpy as np
from numba import njit

from physics_sim.core import Force


@njit
def _compute_drag_linear(
    velocities: np.ndarray,
    speeds: np.ndarray,
    drag_coeffs: np.ndarray,
    cross_sections: np.ndarray,
) -> np.ndarray:
    """JIT-compiled linear drag kernel."""
    result = np.zeros_like(velocities)
    mask = speeds[:, 0] > 0.001

    if mask.sum() == 0:
        return result

    k = drag_coeffs[mask] * cross_sections[mask]
    result[mask] = velocities[mask] * -k[:, np.newaxis]

    return result


@njit
def _compute_drag_quadratic(
    velocities: np.ndarray,
    speeds: np.ndarray,
    fluid_density: float,
    drag_coeffs: np.ndarray,
    cross_sections: np.ndarray,
) -> np.ndarray:
    """JIT-compiled quadratic drag kernel."""
    result = np.zeros_like(velocities)
    mask = speeds[:, 0] > 0.001

    if mask.sum() == 0:
        return result

    magnitude = (
        0.5
        * fluid_density
        * (speeds[mask] ** 2)
        * drag_coeffs[mask, np.newaxis]
        * cross_sections[mask, np.newaxis]
    )
    direction = velocities[mask] / speeds[mask]
    result[mask] = direction * (-magnitude)

    return result


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

    @classmethod
    def get_name(cls) -> str:
        return "Drag"

    def apply_force(
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
        # Extract from kwargs before passing to JIT (JIT can't use kwargs.get)
        drag_coeffs = kwargs.get("drag_coeffs", np.ones(len(velocities)))
        cross_sections = kwargs.get("cross_sections", np.ones(len(velocities)))

        speeds = np.linalg.norm(velocities, axis=1, keepdims=True)

        if self.linear:
            return _compute_drag_linear(
                velocities,
                speeds,
                drag_coeffs,
                cross_sections,
            )
        else:
            return _compute_drag_quadratic(
                velocities,
                speeds,
                self.fluid_density,
                drag_coeffs,
                cross_sections,
            )

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
