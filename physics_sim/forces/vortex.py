from __future__ import annotations

from typing import Any

import numpy as np
from numba import njit

from physics_sim.core import Force


class VortexForce(Force):
    def __init__(
        self,
        center: np.ndarray | list[float] = [10.0, 5.0],
        strength: float = 10.0,
        falloff: float = 1.0,
    ) -> None:
        super().__init__("Vortex")
        self.center = np.asarray(center, dtype=np.float64)
        self.strength = float(strength)
        self.falloff = max(0.0, float(falloff))

    @classmethod
    def get_name(cls) -> str:
        return "Vortex"

    @classmethod
    def is_unique(cls) -> bool:
        return True

    def apply_force(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        return _compute_vortex_force(
            positions=positions,
            center=self.center,
            strength=self.strength,
            falloff=self.falloff,
        )

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        overlays = [
            {
                "kind": "circle",
                "position": self.center.tolist(),
                "radius": max(min(1.0, self.strength / 20.0), 0.2),
                "color": (60, 60, 120),
            }
        ]
        return {"overlays": overlays}

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": [10.0, 5.0],
                "label": "Center [x, y]",
            },
            "strength": {
                "type": "float",
                "default": 10.0,
                "min": 0.0,
                "max": 100.0,
                "label": "Strength",
            },
            "falloff": {
                "type": "float",
                "default": 1.0,
                "min": 0.0,
                "max": 3.0,
                "label": "Falloff (r^-p)",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": self.center.tolist(),
                "label": "Center [x, y]",
            },
            "strength": {
                "type": "float",
                "default": float(self.strength),
                "min": 0.0,
                "max": 100.0,
                "label": "Strength",
            },
            "falloff": {
                "type": "float",
                "default": float(self.falloff),
                "min": 0.0,
                "max": 3.0,
                "label": "Falloff (r^-p)",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        try:
            if "center" in config:
                self.center = np.asarray(config["center"], dtype=np.float64)
            if "strength" in config:
                self.strength = float(config["strength"])
            if "falloff" in config:
                self.falloff = max(0.0, float(config["falloff"]))
            return True
        except (ValueError, TypeError):
            return False

#### END PUBLIC API


@njit
def _compute_vortex_force(
    positions: np.ndarray,
    center: np.ndarray,
    strength: float,
    falloff: float,
) -> np.ndarray:
    n = positions.shape[0]
    result = np.zeros_like(positions)

    for i in range(n):
        dx = positions[i, 0] - center[0]
        dy = positions[i, 1] - center[1]
        r2 = dx * dx + dy * dy
        safe_r2 = r2 if r2 >= 1e-10 else 1e-10
        r = np.sqrt(safe_r2)

        tang_x = -dy
        tang_y = dx
        tan_len = np.sqrt(tang_x * tang_x + tang_y * tang_y)
        safe_tan = tan_len if tan_len >= 1e-10 else 1e-10
        tang_x /= safe_tan
        tang_y /= safe_tan

        falloff_term = r**falloff if falloff != 0.0 else 1.0
        if falloff_term <= 1e-12:
            falloff_term = 1e-12

        magnitude = strength / falloff_term
        result[i, 0] = tang_x * magnitude
        result[i, 1] = tang_y * magnitude

    return result
