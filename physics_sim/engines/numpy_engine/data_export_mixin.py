import numpy as np

from .types import EntityType


class DataExportMixin:
    def get_render_data(self) -> list[dict]:
        render_data: list[dict] = []
        for i in range(self._n_entities):
            entity_type = EntityType(self._entity_types[i])
            base = {
                "id": self._entity_ids[i],
                "type": entity_type.name,
                "position": tuple(self._positions[i]),
            }
            if entity_type == EntityType.BALL:
                base.update({
                    "render_type": "circle",
                    "radius": float(
                        self._type_properties[EntityType.BALL]["radius"][i]
                    ),
                    "color": self._type_properties[EntityType.BALL]["color"][i],
                })
            elif entity_type == EntityType.RECTANGLE_OBSTACLE:
                base.update({
                    "render_type": "rectangle",
                    "width": float(
                        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][i]
                    ),
                    "height": float(
                        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][
                            i
                        ]
                    ),
                    "color": self._type_properties[EntityType.RECTANGLE_OBSTACLE][
                        "color"
                    ][i],
                })
            elif entity_type == EntityType.CIRCLE_OBSTACLE:
                base.update({
                    "render_type": "circle_static",
                    "radius": float(
                        self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][i]
                    ),
                    "color": self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][
                        i
                    ],
                })
            elif entity_type == EntityType.ANCHOR_POINT:
                base.update({
                    "render_type": "circle_static",
                    "radius": float(
                        self._type_properties[EntityType.ANCHOR_POINT]["radius"][i]
                    ),
                    "color": self._type_properties[EntityType.ANCHOR_POINT]["color"][i],
                })
            elif entity_type == EntityType.EXPLOSION_EMITTER:
                base.update({
                    "render_type": "circle_static",
                    "radius": float(
                        self._type_properties[EntityType.EXPLOSION_EMITTER]["radius"][i]
                    ),
                    "color": self._type_properties[EntityType.EXPLOSION_EMITTER][
                        "color"
                    ][i],
                })
            render_data.append(base)
        return render_data

    def get_inventory_data(self) -> list[dict]:
        data: list[dict] = []
        for i in range(self._n_entities):
            if not self._dynamic_mask[i]:
                continue
            entity_type = EntityType(self._entity_types[i])
            entry = {
                "id": self._entity_ids[i],
                "type": entity_type.name,
                "mass": float(self._masses[i]),
                "position": tuple(self._positions[i]),
                "velocity": tuple(self._velocities[i]),
                "speed": float(np.linalg.norm(self._velocities[i])),
                "acceleration": tuple(self._accelerations[i]),
                "applied_forces": [
                    {
                        "name": name,
                        "vector": tuple(vec),
                        "magnitude": float(np.linalg.norm(vec)),
                    }
                    for name, vec in self._applied_forces[i]
                ],
            }
            if entity_type == EntityType.BALL:
                entry["radius"] = float(
                    self._type_properties[EntityType.BALL]["radius"][i]
                )
                entry["restitution"] = float(self._restitutions[i])
            data.append(entry)
        return data

    def get_entity_counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for i in range(self._n_entities):
            name = EntityType(self._entity_types[i]).name
            counts[name] = counts.get(name, 0) + 1
        return counts
