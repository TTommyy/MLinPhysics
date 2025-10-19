from typing import Any

import numpy as np

from physics_sim.core import Force


class PairwiseDistancePBDFore(Force):
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
        n = len(positions)
        if n < 2:
            return positions

        # Compute pairwise distances (O(n^2)) and nearest neighbor within max_distance
        # For moderate n typical in UI, acceptable. Could be optimized later.
        diffs = positions[:, None, :] - positions[None, :, :]
        dists = np.linalg.norm(diffs, axis=2) + np.eye(n) * 1e9

        nearest_idx = np.argmin(dists, axis=1)
        nearest_dist = dists[np.arange(n), nearest_idx]

        updated = positions.copy()
        for i in range(n):
            j = int(nearest_idx[i])
            d = float(nearest_dist[i])
            if d > self.max_distance or d <= 1e-10:
                continue
            delta = positions[i] - positions[j]
            dir_ = delta / d
            corr = self.rest_length - d
            # Split correction by inverse masses (simple equal split for now)
            updated[i] += 0.5 * dir_ * corr
            updated[j] -= 0.5 * dir_ * corr

        return updated

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
