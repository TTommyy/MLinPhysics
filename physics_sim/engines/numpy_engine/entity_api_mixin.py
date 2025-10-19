import numpy as np
from physics_sim.core import Entity
from physics_sim.entities import Ball, CircleObstacle, RectangleObstacle
from .types import EntityType


class EntityApiMixin:
    def add_entity(self, entity: Entity) -> None:
        if self._n_entities >= self._capacity:
            self._grow_arrays()
        idx = self._n_entities
        entity_id = entity.id
        if isinstance(entity, Ball):
            self._add_ball(entity, idx)
        elif isinstance(entity, RectangleObstacle):
            self._add_rectangle_obstacle(entity, idx)
        elif isinstance(entity, CircleObstacle):
            self._add_circle_obstacle(entity, idx)
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")
        self._entity_ids[idx] = entity_id
        self._id_to_index[entity_id] = idx
        self._n_entities += 1

    def _add_ball(self, ball: Ball, idx: int) -> None:
        self._positions[idx] = ball.position
        self._entity_types[idx] = EntityType.BALL
        self._is_static[idx] = False
        self._dynamic_mask[idx] = True
        self._velocities[idx] = ball.velocity
        self._masses[idx] = ball.mass
        self._restitutions[idx] = ball.restitution
        self._drag_coeffs[idx] = ball.drag_coefficient
        self._cross_sections[idx] = ball.cross_sectional_area
        self._friction_coeffs[idx] = ball.friction_coefficient
        self._type_properties[EntityType.BALL]["radius"][idx] = ball.radius
        self._type_properties[EntityType.BALL]["color"][idx] = ball.color

    def _add_rectangle_obstacle(self, obstacle: RectangleObstacle, idx: int) -> None:
        self._positions[idx] = np.array([
            obstacle.position.x
            if hasattr(obstacle.position, "x")
            else obstacle.position[0],
            obstacle.position.y
            if hasattr(obstacle.position, "y")
            else obstacle.position[1],
        ])
        self._entity_types[idx] = EntityType.RECTANGLE_OBSTACLE
        self._is_static[idx] = True
        self._dynamic_mask[idx] = False
        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][idx] = (
            obstacle.width
        )
        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][idx] = (
            obstacle.height
        )
        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["color"][idx] = (
            obstacle.color
        )
        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["friction_coefficient"][
            idx
        ] = obstacle.friction_coefficient
        self._friction_coeffs[idx] = obstacle.friction_coefficient

    def _add_circle_obstacle(self, obstacle: CircleObstacle, idx: int) -> None:
        self._positions[idx] = np.array([
            obstacle.position.x
            if hasattr(obstacle.position, "x")
            else obstacle.position[0],
            obstacle.position.y
            if hasattr(obstacle.position, "y")
            else obstacle.position[1],
        ])
        self._entity_types[idx] = EntityType.CIRCLE_OBSTACLE
        self._is_static[idx] = True
        self._dynamic_mask[idx] = False
        self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][idx] = (
            obstacle.radius
        )
        self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][idx] = obstacle.color
        self._type_properties[EntityType.CIRCLE_OBSTACLE]["friction_coefficient"][
            idx
        ] = obstacle.friction_coefficient

    def remove_entity(self, entity_id: str) -> None:
        if entity_id not in self._id_to_index:
            return
        idx = self._id_to_index[entity_id]
        last_idx = self._n_entities - 1
        if idx != last_idx:
            self._positions[idx] = self._positions[last_idx]
            self._entity_types[idx] = self._entity_types[last_idx]
            self._is_static[idx] = self._is_static[last_idx]
            self._dynamic_mask[idx] = self._dynamic_mask[last_idx]
            self._velocities[idx] = self._velocities[last_idx]
            self._accelerations[idx] = self._accelerations[last_idx]
            self._masses[idx] = self._masses[last_idx]
            self._restitutions[idx] = self._restitutions[last_idx]
            self._drag_coeffs[idx] = self._drag_coeffs[last_idx]
            self._cross_sections[idx] = self._cross_sections[last_idx]
            self._friction_coeffs[idx] = self._friction_coeffs[last_idx]
            for _, props in self._type_properties.items():
                for key, arr in props.items():
                    if isinstance(arr, np.ndarray):
                        arr[idx] = arr[last_idx]
                    elif isinstance(arr, list):
                        arr[idx] = arr[last_idx]
            self._entity_ids[idx] = self._entity_ids[last_idx]
            self._id_to_index[self._entity_ids[idx]] = idx
            self._applied_forces[idx] = self._applied_forces[last_idx]
        del self._id_to_index[entity_id]
        self._n_entities -= 1

    def clear(self) -> None:
        self._n_entities = 0
        self._id_to_index.clear()

    def get_supported_entity_types(self) -> list[type]:
        from physics_sim.entities import Ball, CircleObstacle, RectangleObstacle

        return [Ball, RectangleObstacle, CircleObstacle]

    def get_entity_for_editing(self, entity_id: str) -> Entity | None:
        if entity_id not in self._id_to_index:
            return None
        idx = self._id_to_index[entity_id]
        entity_type = EntityType(self._entity_types[idx])
        if entity_type == EntityType.BALL:
            return Ball(
                position=self._positions[idx].copy(),
                velocity=self._velocities[idx].copy(),
                radius=float(self._type_properties[EntityType.BALL]["radius"][idx]),
                mass=float(self._masses[idx]),
                color=self._type_properties[EntityType.BALL]["color"][idx],
                restitution=float(self._restitutions[idx]),
                drag_coefficient=float(self._drag_coeffs[idx]),
                friction_coefficient=float(self._friction_coeffs[idx]),
                entity_id=entity_id,
            )
        if entity_type == EntityType.RECTANGLE_OBSTACLE:
            return RectangleObstacle(
                position=self._positions[idx].copy(),
                width=float(
                    self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][idx]
                ),
                height=float(
                    self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][idx]
                ),
                color=self._type_properties[EntityType.RECTANGLE_OBSTACLE]["color"][
                    idx
                ],
                friction_coefficient=float(self._friction_coeffs[idx]),
                entity_id=entity_id,
            )
        if entity_type == EntityType.CIRCLE_OBSTACLE:
            return CircleObstacle(
                position=self._positions[idx].copy(),
                radius=float(
                    self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][idx]
                ),
                color=self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][idx],
                friction_coefficient=float(self._friction_coeffs[idx]),
                entity_id=entity_id,
            )
        return None

    def update_entity_from_object(self, entity: Entity) -> bool:
        if entity.id not in self._id_to_index:
            return False
        idx = self._id_to_index[entity.id]
        if isinstance(entity, Ball):
            self._positions[idx] = entity.position
            self._velocities[idx] = entity.velocity
            self._masses[idx] = entity.mass
            self._restitutions[idx] = entity.restitution
            self._drag_coeffs[idx] = entity.drag_coefficient
            self._cross_sections[idx] = entity.cross_sectional_area
            self._friction_coeffs[idx] = entity.friction_coefficient
            self._type_properties[EntityType.BALL]["radius"][idx] = entity.radius
            self._type_properties[EntityType.BALL]["color"][idx] = entity.color
        elif isinstance(entity, RectangleObstacle):
            self._positions[idx] = entity.position
            self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][idx] = (
                entity.width
            )
            self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][idx] = (
                entity.height
            )
            self._type_properties[EntityType.RECTANGLE_OBSTACLE]["color"][idx] = (
                entity.color
            )
            self._type_properties[EntityType.RECTANGLE_OBSTACLE][
                "friction_coefficient"
            ][idx] = entity.friction_coefficient
            self._friction_coeffs[idx] = entity.friction_coefficient
        elif isinstance(entity, CircleObstacle):
            self._positions[idx] = entity.position
            self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][idx] = (
                entity.radius
            )
            self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][idx] = (
                entity.color
            )
            self._type_properties[EntityType.CIRCLE_OBSTACLE]["friction_coefficient"][
                idx
            ] = entity.friction_coefficient
            self._friction_coeffs[idx] = entity.friction_coefficient
        else:
            return False
        return True
