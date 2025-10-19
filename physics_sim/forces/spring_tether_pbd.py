from typing import Any

import numpy as np

from physics_sim.core import Force


class SpringTetherPBDFore(Force):
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
        deltas = positions - self.center
        return -self.k * deltas

    def apply_constraints(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        deltas = positions - self.center
        dist = np.linalg.norm(deltas, axis=1, keepdims=True)
        safe = np.maximum(dist, 1e-10)
        dirs = deltas / safe
        corr = self.rest_length - dist
        return positions + (dirs * corr)

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
