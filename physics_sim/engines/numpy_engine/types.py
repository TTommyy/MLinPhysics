from enum import IntEnum

from physics_sim.entities import (
    AnchorPoint,
    Ball,
    CircleObstacle,
    ExplosionEmitter,
    RectangleObstacle,
)


class EntityType(IntEnum):
    BALL = 0
    RECTANGLE_OBSTACLE = 1
    CIRCLE_OBSTACLE = 2
    ANCHOR_POINT = 3
    EXPLOSION_EMITTER = 4


# // Automated mapping registries for future extensibility
ENTITY_CLASS_TO_TYPE: dict[type, EntityType] = {
    Ball: EntityType.BALL,
    RectangleObstacle: EntityType.RECTANGLE_OBSTACLE,
    CircleObstacle: EntityType.CIRCLE_OBSTACLE,
    AnchorPoint: EntityType.ANCHOR_POINT,
    ExplosionEmitter: EntityType.EXPLOSION_EMITTER,
}

ENTITY_TYPE_TO_CLASS: dict[EntityType, type] = {
    EntityType.BALL: Ball,
    EntityType.RECTANGLE_OBSTACLE: RectangleObstacle,
    EntityType.CIRCLE_OBSTACLE: CircleObstacle,
    EntityType.ANCHOR_POINT: AnchorPoint,
    EntityType.EXPLOSION_EMITTER: ExplosionEmitter,
}
