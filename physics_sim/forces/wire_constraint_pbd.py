from typing import Any, Sequence

import numpy as np

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
    ) -> tuple[np.ndarray, np.ndarray]:
        """Project positions onto circle of fixed radius."""
        deltas = positions - self.center
        dist = np.linalg.norm(deltas, axis=1, keepdims=True)
        safe = np.maximum(dist, 1e-10)
        dirs = deltas / safe
        corr = self.radius - dist
        positions = positions + (dirs * corr)
        return positions

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
