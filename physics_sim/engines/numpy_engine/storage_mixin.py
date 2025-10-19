import numpy as np
from .constants import INITIAL_CAPACITY
from .types import EntityType


class StorageMixin:
    def __init__(self) -> None:
        self._n_entities: int = 0
        self._capacity: int = INITIAL_CAPACITY

        self._positions: np.ndarray = np.zeros((self._capacity, 2), dtype=np.float64)
        self._entity_types: np.ndarray = np.zeros(self._capacity, dtype=np.int32)
        self._is_static: np.ndarray = np.zeros(self._capacity, dtype=bool)

        self._dynamic_mask: np.ndarray = np.zeros(self._capacity, dtype=bool)
        self._velocities: np.ndarray = np.zeros((self._capacity, 2), dtype=np.float64)
        self._accelerations: np.ndarray = np.zeros(
            (self._capacity, 2), dtype=np.float64
        )
        self._masses: np.ndarray = np.zeros(self._capacity, dtype=np.float64)
        self._restitutions: np.ndarray = np.zeros(self._capacity, dtype=np.float64)
        self._drag_coeffs: np.ndarray = np.zeros(self._capacity, dtype=np.float64)
        self._cross_sections: np.ndarray = np.zeros(self._capacity, dtype=np.float64)
        self._friction_coeffs: np.ndarray = np.zeros(self._capacity, dtype=np.float64)

        self._type_properties: dict[EntityType, dict] = {
            EntityType.BALL: {
                "radius": np.zeros(self._capacity, dtype=np.float64),
                "color": [None] * self._capacity,
            },
            EntityType.RECTANGLE_OBSTACLE: {
                "width": np.zeros(self._capacity, dtype=np.float64),
                "height": np.zeros(self._capacity, dtype=np.float64),
                "color": [None] * self._capacity,
                "friction_coefficient": np.zeros(self._capacity, dtype=np.float64),
            },
            EntityType.CIRCLE_OBSTACLE: {
                "radius": np.zeros(self._capacity, dtype=np.float64),
                "color": [None] * self._capacity,
                "friction_coefficient": np.zeros(self._capacity, dtype=np.float64),
            },
        }

        self._entity_ids: list[str] = [None] * self._capacity
        self._id_to_index: dict[str, int] = {}

        self._applied_forces: list[list[tuple[str, np.ndarray]]] = [
            [] for _ in range(self._capacity)
        ]

    def _grow_arrays(self, min_additional: int = 1) -> None:
        new_capacity = max(self._capacity * 2, self._capacity + min_additional)

        self._positions = np.resize(self._positions, (new_capacity, 2))
        self._entity_types = np.resize(self._entity_types, new_capacity)
        self._is_static = np.resize(self._is_static, new_capacity)

        self._dynamic_mask = np.resize(self._dynamic_mask, new_capacity)
        self._velocities = np.resize(self._velocities, (new_capacity, 2))
        self._accelerations = np.resize(self._accelerations, (new_capacity, 2))
        self._masses = np.resize(self._masses, new_capacity)
        self._restitutions = np.resize(self._restitutions, new_capacity)
        self._drag_coeffs = np.resize(self._drag_coeffs, new_capacity)
        self._cross_sections = np.resize(self._cross_sections, new_capacity)
        self._friction_coeffs = np.resize(self._friction_coeffs, new_capacity)

        for _, props in self._type_properties.items():
            for key, arr in props.items():
                if isinstance(arr, np.ndarray):
                    props[key] = np.resize(arr, new_capacity)
                elif isinstance(arr, list):
                    props[key].extend([None] * (new_capacity - self._capacity))

        self._entity_ids.extend([None] * (new_capacity - self._capacity))
        self._applied_forces.extend([[] for _ in range(new_capacity - self._capacity)])

        self._capacity = new_capacity
