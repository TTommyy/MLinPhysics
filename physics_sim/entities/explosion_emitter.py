from typing import Any

import numpy as np

from physics_sim.core import Entity


class ExplosionEmitter(Entity):
    def __init__(
        self,
        position: np.ndarray,
        radius: float = 0.25,
        color: tuple[int, int, int] = (160, 60, 60),
        entity_id: str | None = None,
    ) -> None:
        super().__init__(entity_id)
        self.position = np.asarray(position, dtype=np.float64)
        self.radius = float(radius)
        self.color = color
        self.static = True

    @classmethod
    def get_default_parameters(cls) -> dict[str, dict[str, Any]]:
        return {
            "radius": {
                "type": "float",
                "default": 0.25,
                "min": 0.05,
                "max": 3.0,
                "label": "Radius",
            },
            "color": {"type": "color", "default": (160, 60, 60), "label": "Color"},
        }

    def get_settable_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "position": {
                "type": "vector",
                "default": self.position.tolist(),
                "label": "Position [x, y]",
            },
            "radius": {
                "type": "float",
                "default": float(self.radius),
                "min": 0.05,
                "max": 3.0,
                "label": "Radius",
            },
            "color": {"type": "color", "default": self.color, "label": "Color"},
        }

    def update_physics_data(self, config: dict[str, Any]) -> bool:
        try:
            if "position" in config:
                self.position = np.asarray(config["position"], dtype=np.float64)
            if "radius" in config:
                self.radius = float(config["radius"])
            if "color" in config:
                self.color = config["color"]
            return True
        except (ValueError, TypeError):
            return False
