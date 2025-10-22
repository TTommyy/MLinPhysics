__all__: list[str] = [
    "CentralGravityForce",
    "LinearGravityForce",
    "DragForce",
    "WireConstraintPBDForce",
    "VortexForce",
    "SpringTetherPBDFore",
    "ExplosionImpulseForce",
    "PairwiseDistancePBDFore",
]

from .central_gravity import CentralGravityForce
from .drag import DragForce
from .explosion_impulse import ExplosionImpulseForce
from .linear_gravity import LinearGravityForce
from .pairwise_distance_pbd import PairwiseDistancePBDFore
from .spring_tether_pbd import SpringTetherPBDFore
from .vortex import VortexForce
from .wire_constraint_pbd import WireConstraintPBDForce


def get_supported_forces() -> list[type]:
    return [
        CentralGravityForce,
        LinearGravityForce,
        DragForce,
        VortexForce,
        WireConstraintPBDForce,
        SpringTetherPBDFore,
        ExplosionImpulseForce,
        PairwiseDistancePBDFore,
    ]
