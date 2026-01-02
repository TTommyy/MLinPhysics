__all__: list[str] = [
    "CentralGravityForce",
    "LinearGravityForce",
    "DragForce",
    "WireConstraintPBDForce",
    "VortexForce",
    "SpringTetherPBDForce",
    "ExplosionImpulseForce",
    "PairwiseDistancePBDForce",
]

from .central_gravity import CentralGravityForce
from .drag import DragForce
from .explosion_impulse import ExplosionImpulseForce
from .linear_gravity import LinearGravityForce
from .pairwise_distance_pbd import PairwiseDistancePBDForce
from .spring_tether_pbd import SpringTetherPBDForce
from .vortex import VortexForce
from .wire_constraint_pbd import WireConstraintPBDForce


def get_supported_forces() -> list[type]:
    return [
        CentralGravityForce,
        LinearGravityForce,
        DragForce,
        VortexForce,
        WireConstraintPBDForce,
        SpringTetherPBDForce,
        ExplosionImpulseForce,
        PairwiseDistancePBDForce,
    ]
