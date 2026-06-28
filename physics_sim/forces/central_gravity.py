from __future__ import annotations

from typing import Any

import numpy as np
from numba import njit

from physics_sim.core import Force


class CentralGravityForce(Force):
    def __init__(
        self,
        center: np.ndarray | list[float] = np.asarray([10, 5]),
        center_mass: float = 2,
        gravitational_constant: float = 1.0,
    ):
        super().__init__("CentralGravity")
        self.center = np.asarray(center, dtype=np.float64)
        self.center_mass = float(center_mass)
        self.G = float(gravitational_constant)

    @classmethod
    def get_name(cls) -> str:
        return "CentralGravity"

    def apply_force(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        return _compute_central_gravity_force(
            positions=positions,
            masses=masses,
            center=self.center,
            center_mass=self.center_mass,
            G=self.G,
        )

    def get_potential_energy_contribution(
        self,
        positions: np.ndarray,
        masses: np.ndarray,
        **kwargs,
    ) -> float:
        return _compute_central_gravity_potential(
            positions=positions,
            masses=masses,
            center=self.center,
            center_mass=self.center_mass,
            G=self.G,
        )

    @classmethod
    def is_unique(cls) -> bool:
        return True

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": [10.0, 5.0],
                "label": "Center [x, y]",
            },
            "center_mass": {
                "type": "float",
                "default": 2,
                "min": 1.0,
                "max": 1e12,
                "label": "Center Mass (kg)",
            },
            "gravitational_constant": {
                "type": "float",
                "default": 1.0,
                "min": 1e-6,
                "max": 100.0,
                "label": "G",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": self.center.tolist(),
                "label": "Center [x, y]",
            },
            "center_mass": {
                "type": "float",
                "default": float(self.center_mass),
                "min": 1.0,
                "max": 1e12,
                "label": "Center Mass (kg)",
            },
            "gravitational_constant": {
                "type": "float",
                "default": float(self.G),
                "min": 1e-6,
                "max": 100.0,
                "label": "G",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        try:
            if "center" in config:
                self.center = np.asarray(config["center"], dtype=np.float64)
            if "center_mass" in config:
                self.center_mass = float(config["center_mass"])
            if "gravitational_constant" in config:
                self.G = float(config["gravitational_constant"])
            return True
        except (ValueError, TypeError):
            return False

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        overlays = [
            {
                "kind": "circle",
                "position": self.center.tolist(),
                "radius": max(min(1, (self.G * self.center_mass) / 20), 0.1),
                "color": (60, 60, 60),
            },
            {
                "kind": "text",
                "position": self.center.tolist(),
                "text": f"M={self.center_mass}",
                "color": (30, 30, 30),
                "size": 10,
            },
        ]
        return {"overlays": overlays}


#### END PUBLIC API


@njit
def _compute_central_gravity_force(
    positions: np.ndarray,
    masses: np.ndarray,
    center: np.ndarray,
    center_mass: float,
    G: float,
) -> np.ndarray:
    n = positions.shape[0]
    result = np.zeros_like(positions)

    for i in range(n):
        dx = center[0] - positions[i, 0]
        dy = center[1] - positions[i, 1]
        r2 = dx * dx + dy * dy
        if r2 < 1e-10:
            r2 = 1e-10
        magnitude = G * center_mass * masses[i] / r2
        result[i, 0] = dx * magnitude
        result[i, 1] = dy * magnitude

    return result


@njit
def _compute_central_gravity_potential(
    positions: np.ndarray,
    masses: np.ndarray,
    center: np.ndarray,
    center_mass: float,
    G: float,
) -> float:
    n = positions.shape[0]
    energy = 0.0

    for i in range(n):
        dx = center[0] - positions[i, 0]
        dy = center[1] - positions[i, 1]
        r2 = dx * dx + dy * dy
        safe_r2 = r2 if r2 >= 1e-10 else 1e-10
        r = np.sqrt(safe_r2)
        energy -= G * center_mass * masses[i] / r

    return energy
