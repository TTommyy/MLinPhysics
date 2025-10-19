from typing import Any

import numpy as np

from physics_sim.core import Force


class CentralGravityForce(Force):
    def __init__(
        self,
        center: np.ndarray = [10, 5],
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
        deltas = self.center - positions
        r2 = np.sum(deltas**2, axis=1, keepdims=True)
        r2 = np.maximum(r2, 1e-10)
        r = np.sqrt(r2)
        directions = deltas / r
        magnitudes = self.G * self.center_mass * masses[:, np.newaxis] / r2
        return directions * magnitudes

    def get_potential_energy_contribution(
        self,
        positions: np.ndarray,
        masses: np.ndarray,
        **kwargs,
    ) -> float:
        deltas = self.center - positions
        r = np.linalg.norm(deltas, axis=1)
        r = np.maximum(r, 1e-10)
        return float(-self.G * self.center_mass * np.sum(masses / r))

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
