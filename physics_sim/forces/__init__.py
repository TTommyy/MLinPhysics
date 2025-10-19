__all__: list[str] = [
    "LinearGravityForce",
    "DragForce",
]

from .drag import DragForce
from .gravity import LinearGravityForce


def get_supported_forces() -> list[type]:
    return [DragForce, LinearGravityForce]
