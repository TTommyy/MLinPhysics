from __future__ import annotations

from typing import Any

import numpy as np
from numba import njit

from physics_sim.core import Force


class PairwiseDistancePBDForce(Force):
    """PBD constraint to keep nearby dynamic entities at a target distance.

    Strategy: connect each entity to its nearest neighbor within max_distance.
    """

    def __init__(self, rest_length: float = 1.5, max_distance: float = 2.0):
        super().__init__("PairwiseDistancePBD")
        self.rest_length = float(rest_length)
        self.max_distance = float(max_distance)

    @classmethod
    def get_name(cls) -> str:
        return "PairwiseDistancePBD"

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
        # Force-less; constraint handled in apply_constraints
        return np.zeros_like(positions)

    def apply_constraints(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        return _relax_pairwise_distance_positions(
            positions=positions,
            rest_length=self.rest_length,
            max_distance=self.max_distance,
        )

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        # No vector field defined; constraints only. Provide empty.
        return {}

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        return {
            "rest_length": {
                "type": "float",
                "default": 1.5,
                "min": 0.0,
                "max": 10.0,
                "label": "Rest length",
            },
            "max_distance": {
                "type": "float",
                "default": 2.0,
                "min": 0.0,
                "max": 10.0,
                "label": "Max distance",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "rest_length": {
                "type": "float",
                "default": float(self.rest_length),
                "min": 0.0,
                "max": 10.0,
                "label": "Rest length",
            },
            "max_distance": {
                "type": "float",
                "default": float(self.max_distance),
                "min": 0.0,
                "max": 10.0,
                "label": "Max distance",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        try:
            if "rest_length" in config:
                self.rest_length = float(config["rest_length"])
            if "max_distance" in config:
                self.max_distance = float(config["max_distance"])
            return True
        except (ValueError, TypeError):
            return False


#### END PUBLIC API


@njit
def _relax_pairwise_distance_positions(
    positions: np.ndarray,
    rest_length: float,
    max_distance: float,
) -> np.ndarray:
    n = positions.shape[0]
    updated = positions.copy()
    if n < 2:
        return updated

    for i in range(n):
        nearest_j = -1
        nearest_dist = 1e18
        for j in range(n):
            if i == j:
                continue
            dx = positions[i, 0] - positions[j, 0]
            dy = positions[i, 1] - positions[j, 1]
            dist = np.sqrt(dx * dx + dy * dy)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_j = j

        if nearest_j < 0:
            continue

        d = nearest_dist
        if d > max_distance or d <= 1e-10:
            continue

        dx = positions[i, 0] - positions[nearest_j, 0]
        dy = positions[i, 1] - positions[nearest_j, 1]
        dir_x = dx / d
        dir_y = dy / d
        corr = rest_length - d
        updated[i, 0] += 0.5 * dir_x * corr
        updated[i, 1] += 0.5 * dir_y * corr
        updated[nearest_j, 0] -= 0.5 * dir_x * corr
        updated[nearest_j, 1] -= 0.5 * dir_y * corr

    return updated
