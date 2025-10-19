__all__: list[str] = [
    "CentralGravityForce",
    "LinearGravityForce",
    "DragForce",
]

from .central_gravity import CentralGravityForce
from .drag import DragForce
from .linear_gravity import LinearGravityForce


def get_supported_forces() -> list[type]:
    return [CentralGravityForce, LinearGravityForce, DragForce]
