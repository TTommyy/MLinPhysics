import pymunk

from physics_sim.core.engine import PhysicsEngine
from physics_sim.core.entity import Entity
from physics_sim.core.vector import Vector2D
from physics_sim.entities.ball import Ball


class PymunkPhysicsEngine(PhysicsEngine):
    """Physics engine wrapping the Pymunk library.

    Pymunk is a 2D physics library that provides:
    - Accurate rigid body dynamics
    - Efficient collision detection
    - Constraint solving
    - Realistic physical interactions

    This implementation wraps Pymunk while maintaining the same
    interface as our custom numpy engine.
    """

    def __init__(self, gravity: Vector2D, bounds: tuple[float, float]):
        super().__init__(gravity, bounds)

        # Create pymunk space
        self.space = pymunk.Space(threaded=True)
        self.space.gravity = (gravity.x, gravity.y)
        self.space.threads = 10

        # Track entity mappings
        self._entities: dict[str, Entity] = {}
        self._entity_bodies: dict[str, pymunk.Body] = {}

        # Create boundary walls
        self._create_boundaries()

    def _create_boundaries(self) -> None:
        """Create static walls at simulation boundaries."""
        width, height = self.bounds

        # Create static body for walls
        static_body = self.space.static_body

        # Wall segments: [bottom, right, top, left]
        walls = [
            pymunk.Segment(static_body, (0, 0), (width, 0), 0.1),
            pymunk.Segment(static_body, (width, 0), (width, height), 0.1),
            pymunk.Segment(static_body, (width, height), (0, height), 0.1),
            pymunk.Segment(static_body, (0, height), (0, 0), 0.1),
        ]

        for wall in walls:
            wall.elasticity = 1.0  # Fully elastic collisions
            wall.friction = 0.0  # No friction by default
            # TODO: Add friction coefficient for more realistic behavior

        self.space.add(*walls)

    def add_entity(self, entity: Entity) -> None:
        """Add entity to simulation by creating corresponding pymunk body."""
        self._entities[entity.id] = entity

        if isinstance(entity, Ball):
            self._add_ball(entity)
        # TODO: Add support for other entity types (obstacles, etc.)

    def _add_ball(self, ball: Ball) -> None:
        """Create pymunk body and shape for a ball."""
        # Create dynamic body
        moment = pymunk.moment_for_circle(ball.mass, 0, ball.radius)
        body = pymunk.Body(ball.mass, moment)
        body.position = (ball.position.x, ball.position.y)
        body.velocity = (ball.velocity.x, ball.velocity.y)

        # Create circle shape
        shape = pymunk.Circle(body, ball.radius)
        shape.elasticity = ball.restitution
        shape.friction = 0.0  # TODO: Use ball.friction when implemented

        # Store reference to original ball for updates
        body.ball_ref = ball

        self.space.add(body, shape)
        self._entity_bodies[ball.id] = body

    def remove_entity(self, entity_id: str) -> None:
        """Remove entity and its pymunk body from simulation."""
        if entity_id in self._entities:
            del self._entities[entity_id]

        if entity_id in self._entity_bodies:
            body = self._entity_bodies[entity_id]
            self.space.remove(body, *body.shapes)
            del self._entity_bodies[entity_id]

    def get_entities(self) -> list[Entity]:
        return list(self._entities.values())

    def clear(self) -> None:
        """Remove all entities from the simulation."""
        for entity_id in list(self._entity_bodies.keys()):
            self.remove_entity(entity_id)
        self._entities.clear()

    def step(self, dt: float) -> None:
        """Advance simulation using pymunk's solver with custom forces."""
        # Apply custom forces to entities
        for entity_id, entity in self._entities.items():
            if isinstance(entity, Ball) and entity_id in self._entity_bodies:
                body = self._entity_bodies[entity_id]
                self._apply_forces_to_ball(entity, body, dt)

        # Step the pymunk space
        self.space.step(dt)

        # Sync pymunk state back to our entity objects
        for entity_id, body in self._entity_bodies.items():
            entity = self._entities[entity_id]
            if isinstance(entity, Ball):
                entity.position.x = body.position.x
                entity.position.y = body.position.y
                entity.velocity.x = body.velocity.x
                entity.velocity.y = body.velocity.y

    def _apply_forces_to_ball(self, ball: Ball, body: pymunk.Body, dt: float) -> None:
        """Apply custom forces to a ball in the pymunk simulation."""
        ball.reset_acceleration()
        ball.clear_force_tracking()

        # Apply all registered forces
        for force in self.forces:
            if force.should_apply_to(ball):
                force_vector = force.apply_to(ball, dt)
                ball.apply_force(force_vector)
                ball.track_force(force.name, force_vector)

        # Apply the accumulated acceleration to the pymunk body
        acceleration = ball.get_acceleration()
        if acceleration.magnitude() > 0.001:  # Only apply if significant
            # Apply force as impulse: F * dt = m * dv, so dv = (F * dt) / m
            impulse = acceleration * dt * ball.mass
            body.apply_impulse_at_local_point((impulse.x, impulse.y), (0, 0))

    # TODO: Add collision handlers for custom collision behavior
    #
    # def add_collision_handler(self, type_a: int, type_b: int, callback):
    #     """Register a callback for collisions between two entity types."""
    #     handler = self.space.add_collision_handler(type_a, type_b)
    #     handler.begin = callback
    #
    # Example usage:
    #     def on_ball_collision(arbiter, space, data):
    #         # Custom behavior when balls collide
    #         return True
    #
    #     engine.add_collision_handler(BALL_TYPE, BALL_TYPE, on_ball_collision)
