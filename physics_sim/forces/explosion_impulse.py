from typing import Any

import numpy as np

from physics_sim.core import Force


class ExplosionImpulseForce(Force):
    def __init__(
        self,
        center: np.ndarray | list[float] = [10.0, 5.0],
        peak_impulse: float = 50.0,
        duration: float = 0.3,
        falloff: float = 1.0,
    ) -> None:
        super().__init__("Explosion")
        self.center = np.asarray(center, dtype=np.float64)
        self.peak_impulse = float(peak_impulse)
        self.duration = max(1e-6, float(duration))
        self.falloff = max(0.0, float(falloff))
        self._time = 0.0

    @classmethod
    def get_name(cls) -> str:
        return "Explosion"

    @classmethod
    def is_unique(cls) -> bool:
        return False

    def apply_force(
        self,
        positions: np.ndarray,
        velocities: np.ndarray,
        masses: np.ndarray,
        entity_types: np.ndarray,
        dt: float,
        **kwargs,
    ) -> np.ndarray:
        # Simple time-boxed impulse distributed as force over this frame
        if dt > 0:
            self._time += dt
        if self._time > self.duration:
            return np.zeros_like(positions)

        deltas = positions - self.center
        r2 = np.sum(deltas**2, axis=1, keepdims=True)
        r = np.sqrt(np.maximum(r2, 1e-10))
        dirs = deltas / r

        # Temporal envelope (e.g., triangular decay)
        t_norm = max(0.0, 1.0 - self._time / self.duration)
        impulse_mag = self.peak_impulse * t_norm
        # Convert impulse to force over dt; add radial falloff
        magnitude = (impulse_mag / max(dt, 1e-6)) / (r**self.falloff)
        return dirs * magnitude

    def get_render_data(self, sample_points: np.ndarray) -> dict[str, Any]:
        t_norm = max(0.0, 1.0 - self._time / self.duration)
        overlays = [
            {
                "kind": "circle",
                "position": self.center.tolist(),
                "radius": max(0.2, (self.peak_impulse * t_norm) / 25.0),
                "color": (160, 60, 60),
            }
        ]
        return {"overlays": overlays}

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        return {
            "center": {"type": "vector", "default": [10.0, 5.0], "label": "Center"},
            "peak_impulse": {
                "type": "float",
                "default": 50.0,
                "min": 0.0,
                "max": 500.0,
                "label": "Peak impulse",
            },
            "duration": {
                "type": "float",
                "default": 0.3,
                "min": 0.05,
                "max": 5.0,
                "label": "Duration (s)",
            },
            "falloff": {
                "type": "float",
                "default": 1.0,
                "min": 0.0,
                "max": 3.0,
                "label": "Radial falloff",
            },
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "center": {
                "type": "vector",
                "default": self.center.tolist(),
                "label": "Center",
            },
            "peak_impulse": {
                "type": "float",
                "default": float(self.peak_impulse),
                "min": 0.0,
                "max": 500.0,
                "label": "Peak impulse",
            },
            "duration": {
                "type": "float",
                "default": float(self.duration),
                "min": 0.05,
                "max": 5.0,
                "label": "Duration (s)",
            },
            "falloff": {
                "type": "float",
                "default": float(self.falloff),
                "min": 0.0,
                "max": 3.0,
                "label": "Radial falloff",
            },
        }

    def update_parameters(self, config: dict[str, Any]) -> bool:
        try:
            if "center" in config:
                self.center = np.asarray(config["center"], dtype=np.float64)
            if "peak_impulse" in config:
                self.peak_impulse = float(config["peak_impulse"])
            if "duration" in config:
                self.duration = max(1e-6, float(config["duration"]))
            if "falloff" in config:
                self.falloff = max(0.0, float(config["falloff"]))
            return True
        except (ValueError, TypeError):
            return False
