from physics_sim.core import Entity, PhysicsEngine, Vector2D
from physics_sim.entities.ball import Ball


class NumpyPhysicsEngine(PhysicsEngine):
    """Custom physics engine using numpy for calculations.

    Implements:
    - Euler integration for position and velocity
    - Gravity application
    - Boundary collision detection and response

    This implementation is educational and demonstrates basic physics
    simulation concepts from first principles.
    """

    def __init__(self, gravity: Vector2D, bounds: tuple[float, float]):
        super().__init__(gravity, bounds)
        self._entities: dict[str, Entity] = {}
        self._paused: bool = False

    def add_entity(self, entity: Entity) -> None:
        self._entities[entity.id] = entity

    def remove_entity(self, entity_id: str) -> None:
        if entity_id in self._entities:
            del self._entities[entity_id]

    def get_entities(self) -> list[Entity]:
        return list(self._entities.values())

    def clear(self) -> None:
        self._entities.clear()

    def step(self, dt: float) -> None:
        """Advance simulation using Euler integration."""
        if self._paused:
            return

        for entity in self._entities.values():
            if isinstance(entity, Ball):
                self._integrate_ball(entity, dt)
                self._handle_boundary_collisions(entity)

    def _integrate_ball(self, ball: Ball, dt: float) -> None:
        """Euler integration: update velocity and position."""
        ball.reset_acceleration()
        ball.clear_force_tracking()

        # Apply all registered forces
        for force in self.forces:
            if force.should_apply_to(ball):
                force_vector = force.apply_to(ball, dt)
                ball.apply_force(force_vector)
                ball.track_force(force.name, force_vector)

        # Update velocity: v = v + a * dt
        acceleration = ball.get_acceleration()
        ball.velocity = ball.velocity + acceleration * dt

        # Update position: p = p + v * dt
        ball.position = ball.position + ball.velocity * dt

    def _handle_boundary_collisions(self, ball: Ball) -> None:
        """Detect and resolve collisions with simulation boundaries."""
        width, height = self.bounds

        # Left boundary
        if ball.position.x - ball.radius < 0:
            ball.position.x = ball.radius
            ball.velocity.x = -ball.velocity.x * ball.restitution

        # Right boundary
        if ball.position.x + ball.radius > width:
            ball.position.x = width - ball.radius
            ball.velocity.x = -ball.velocity.x * ball.restitution

        # Bottom boundary
        if ball.position.y - ball.radius < 0:
            ball.position.y = ball.radius
            ball.velocity.y = -ball.velocity.y * ball.restitution

            # TODO: Apply friction when in contact with ground
            # if abs(ball.velocity.y) < threshold:
            #     ball.velocity.x *= (1 - friction_coefficient)

        # Top boundary (optional, not in original)
        if ball.position.y + ball.radius > height:
            ball.position.y = height - ball.radius
            ball.velocity.y = -ball.velocity.y * ball.restitution

    # TODO: Implement ball-to-ball collision detection and resolution
    #
    # def _handle_ball_collisions(self) -> None:
    #     """Detect and resolve elastic collisions between balls."""
    #     balls = [e for e in self._entities.values() if isinstance(e, Ball)]
    #
    #     for i, ball1 in enumerate(balls):
    #         for ball2 in balls[i+1:]:
    #             distance = (ball2.position - ball1.position).magnitude()
    #             min_distance = ball1.radius + ball2.radius
    #
    #             if distance < min_distance:
    #                 # Collision detected - resolve using elastic collision formulas
    #                 # See: https://en.wikipedia.org/wiki/Elastic_collision
    #                 normal = (ball2.position - ball1.position).normalized()
    #
    #                 # Separate balls
    #                 overlap = min_distance - distance
    #                 ball1.position = ball1.position - normal * (overlap / 2)
    #                 ball2.position = ball2.position + normal * (overlap / 2)
    #
    #                 # Calculate new velocities
    #                 relative_velocity = ball1.velocity - ball2.velocity
    #                 velocity_along_normal = relative_velocity.dot(normal)
    #
    #                 if velocity_along_normal > 0:
    #                     continue  # Balls moving apart
    #
    #                 # Compute impulse
    #                 restitution = min(ball1.restitution, ball2.restitution)
    #                 impulse_magnitude = -(1 + restitution) * velocity_along_normal
    #                 impulse_magnitude /= (1/ball1.mass + 1/ball2.mass)
    #
    #                 impulse = normal * impulse_magnitude
    #                 ball1.velocity = ball1.velocity - impulse / ball1.mass
    #                 ball2.velocity = ball2.velocity + impulse / ball2.mass

    def pause(self) -> None:
        self._paused = True

    def is_paused(self) -> bool:
        return self._paused

    def toggle_pause(self) -> None:
        self._paused = not self._paused
