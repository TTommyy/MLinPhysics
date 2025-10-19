from typing import Any

import numpy as np

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
        deltas = positions - self.center
        r2 = np.sum(deltas**2, axis=1, keepdims=True)
        r = np.sqrt(np.maximum(r2, 1e-10))
        # Perpendicular (tangential) directions: rotate by +90deg
        tangents = np.concatenate((-deltas[:, 1:2], deltas[:, 0:1]), axis=1)
        tangents /= np.maximum(np.linalg.norm(tangents, axis=1, keepdims=True), 1e-10)

        magnitude = self.strength / (r**self.falloff)
        return tangents * magnitude

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
