import os as _os

# Kivy reads these at import time; configure before any kivy import happens.
# - KIVY_NO_ARGS: do not let Kivy parse sys.argv (pytest / CLI arguments).
# - KIVY_LOG_MODE=PYTHON: keep the application's own logging configuration.
_os.environ.setdefault("KIVY_NO_ARGS", "1")
_os.environ.setdefault("KIVY_LOG_MODE", "PYTHON")

__all__: list[str] = [
    "Entity",
    "PhysicalEntity",
    "PhysicsEngine",
    "Ball",
    "RectangleObstacle",
    "CircleObstacle",
    "NumpyPhysicsEngine",
    "Renderer",
    "KivyRenderer",
    "Force",
    "LinearGravityForce",
    "DragForce",
    "SimulationConfig",
    "Simulator",
]

from physics_sim.core import (
    Entity,
    Force,
    PhysicalEntity,
    PhysicsEngine,
    Renderer,
)
from physics_sim.engines import NumpyPhysicsEngine
from physics_sim.entities import Ball, CircleObstacle, RectangleObstacle
from physics_sim.forces import DragForce, LinearGravityForce
from physics_sim.simulation.config import SimulationConfig


def __getattr__(name: str):
    """Lazily import Kivy dependent objects.

    Importing Kivy's window module opens a window, so the renderer and the
    simulator are only imported when actually requested. This keeps the
    engine/entities/forces usable headless (tests, notebooks).
    """
    if name == "KivyRenderer":
        from physics_sim.rendering import KivyRenderer

        return KivyRenderer
    if name == "Simulator":
        from physics_sim.simulation.simulator import Simulator

        return Simulator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
