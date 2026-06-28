from __future__ import annotations

from typing import Any

import numpy as np
from numba import njit

from physics_sim.core import Force


class SpringTetherPBDForce(Force):
    def __init__(
        self,
        center: np.ndarray | list[float] = [10.0, 5.0],
        spring_k: float = 5.0,
        rest_length: float = 2.0,
    ) -> None:
        super().__init__("SpringTetherPBD")
        self.center = np.asarray(center, dtype=np.float64)
        self.k = float(spring_k)
        self.rest_length = float(rest_length)

    @classmethod
    def get_name(cls) -> str:
        return "SpringTetherPBD"

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
        return _compute_spring_tether_force(
            positions=positions,
            center=self.center,
            stiffness=self.k,
        )

    def apply_constraints(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        return _apply_spring_tether_constraints(
            positions=positions,
            center=self.center,
            rest_length=self.rest_length,
        )

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        overlays = [
            {
                "kind": "dashed_circle",
                "position": self.center.tolist(),
                "radius": float(self.rest_length),
                "color": (80, 80, 80),
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
            "spring_k": {
                "type": "float",
                "default": 5.0,
                "min": 0.0,
                "max": 100.0,
                "label": "Spring k",
            },
            "rest_length": {
                "type": "float",
                "default": 2.0,
                "min": 0.0,
                "max": 10.0,
                "label": "Rest length",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": self.center.tolist(),
                "label": "Center [x, y]",
            },
            "spring_k": {
                "type": "float",
                "default": float(self.k),
                "min": 0.0,
                "max": 100.0,
                "label": "Spring k",
            },
            "rest_length": {
                "type": "float",
                "default": float(self.rest_length),
                "min": 0.0,
                "max": 10.0,
                "label": "Rest length",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        try:
            if "center" in config:
                self.center = np.asarray(config["center"], dtype=np.float64)
            if "spring_k" in config:
                self.k = float(config["spring_k"])
            if "rest_length" in config:
                self.rest_length = float(config["rest_length"])
            return True
        except (ValueError, TypeError):
            return False


#### END PUBLIC API


@njit
def _compute_spring_tether_force(
    positions: np.ndarray,
    center: np.ndarray,
    stiffness: float,
) -> np.ndarray:
    n = positions.shape[0]
    result = np.zeros_like(positions)
    for i in range(n):
        result[i, 0] = -stiffness * (positions[i, 0] - center[0])
        result[i, 1] = -stiffness * (positions[i, 1] - center[1])
    return result


@njit
def _apply_spring_tether_constraints(
    positions: np.ndarray,
    center: np.ndarray,
    rest_length: float,
) -> np.ndarray:
    n = positions.shape[0]
    updated = positions.copy()
    for i in range(n):
        dx = positions[i, 0] - center[0]
        dy = positions[i, 1] - center[1]
        dist_sq = dx * dx + dy * dy
        dist = np.sqrt(dist_sq)
        safe = dist if dist >= 1e-10 else 1e-10
        dir_x = dx / safe
        dir_y = dy / safe
        corr = rest_length - dist
        updated[i, 0] += dir_x * corr
        updated[i, 1] += dir_y * corr
    return updated
