__all__: list[str] = [
    "Force",
    "LinearGravityForce",
    "DragForce",
    "ThrustForce",
    "EntitySpecificForce",
]

from physics_sim.core import Force

from .custom_force import EntitySpecificForce
from .drag import DragForce
from .gravity import LinearGravityForce
from .thrust import ThrustForce


def get_supported_forces() -> list[type]:
    return [DragForce, LinearGravityForce]
