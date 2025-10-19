__all__: list[str] = [
    "CentralGravityForce",
    "LinearGravityForce",
    "DragForce",
    "WireConstraintPBDForce",
]

from .central_gravity import CentralGravityForce
from .drag import DragForce
from .linear_gravity import LinearGravityForce
from .wire_constraint_pbd import WireConstraintPBDForce


def get_supported_forces() -> list[type]:
    return [CentralGravityForce, LinearGravityForce, DragForce, WireConstraintPBDForce]
