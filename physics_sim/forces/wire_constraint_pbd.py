from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from numba import njit

from physics_sim.core import Force


class WireConstraintPBDForce(Force):
    """PBD-style wire constraint that keeps entities at fixed distance from center.

    Projects positions onto a circle of given radius, used for orbital/pendulum simulations.
    """

    def __init__(
        self, center: Sequence[float] | np.ndarray = [10, 5], radius: float = 2.5
    ):
        super().__init__("WireConstraintPBD")
        self.center = np.asarray(center, dtype=np.float64)
        self.radius = float(radius)

    @classmethod
    def get_name(cls) -> str:
        return "WireConstraintPBD"

    def apply_constraints(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        """Project positions onto circle of fixed radius."""
        return _project_wire_positions(
            positions=positions,
            center=self.center,
            radius=self.radius,
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
            "radius": {
                "type": "float",
                "default": 2.5,
                "min": 1.0,
                "max": 3.0,
                "label": "Wire Radius",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": self.center.tolist(),
                "label": "Center [x, y]",
            },
            "radius": {
                "type": "float",
                "default": float(self.radius),
                "min": 1.0,
                "max": 3.0,
                "label": "Wire Radius",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        try:
            if "center" in config:
                self.center = np.asarray(config["center"], dtype=np.float64)
            if "radius" in config:
                self.radius = float(config["radius"])
            return True
        except (ValueError, TypeError):
            return False

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        overlays = [
            {
                "kind": "dashed_circle",
                "position": self.center.tolist(),
                "radius": float(self.radius),
                "color": (80, 80, 80),
            }
        ]
        return {"overlays": overlays}


#### END PUBLIC API


@njit
def _project_wire_positions(
    positions: np.ndarray,
    center: np.ndarray,
    radius: float,
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
        corr = radius - dist
        updated[i, 0] += dir_x * corr
        updated[i, 1] += dir_y * corr
    return updated
