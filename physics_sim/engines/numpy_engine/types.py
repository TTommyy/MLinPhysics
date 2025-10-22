from enum import IntEnum

from physics_sim.entities import (
    Ball,
    CircleObstacle,
    RectangleObstacle,
)


class EntityType(IntEnum):
    BALL = 0
    RECTANGLE_OBSTACLE = 1
    CIRCLE_OBSTACLE = 2


# // Automated mapping registries for future extensibility
ENTITY_CLASS_TO_TYPE: dict[type, EntityType] = {
    Ball: EntityType.BALL,
    RectangleObstacle: EntityType.RECTANGLE_OBSTACLE,
    CircleObstacle: EntityType.CIRCLE_OBSTACLE,
}

ENTITY_TYPE_TO_CLASS: dict[EntityType, type] = {
    EntityType.BALL: Ball,
    EntityType.RECTANGLE_OBSTACLE: RectangleObstacle,
    EntityType.CIRCLE_OBSTACLE: CircleObstacle,
}
