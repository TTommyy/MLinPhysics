import numpy as np
from .types import EntityType
from .constants import EPS


class CollisionMixin:
    def _handle_ball_ball_collisions_vectorized(self) -> None:
        n = self._n_entities
        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        ball_indices = np.where(ball_mask)[0]
        if len(ball_indices) < 2:
            return

        positions = self._positions[ball_indices]
        velocities = self._velocities[ball_indices]
        masses = self._masses[ball_indices]
        radii = self._type_properties[EntityType.BALL]["radius"][ball_indices]
        restitutions = self._restitutions[ball_indices]

        n_balls = len(ball_indices)
        for i in range(n_balls):
            for j in range(i + 1, n_balls):
                delta = positions[j] - positions[i]
                distance = np.linalg.norm(delta)
                min_distance = radii[i] + radii[j]
                if distance < min_distance and distance > EPS:
                    normal = delta / distance
                    relative_velocity = velocities[i] - velocities[j]
                    v_normal = np.dot(relative_velocity, normal)
                    if v_normal <= 0:
                        continue

                    restitution = (restitutions[i] + restitutions[j]) / 2.0
                    impulse_scalar = (-(1.0 + restitution) * v_normal) / (
                        1.0 / masses[i] + 1.0 / masses[j]
                    )
                    impulse = impulse_scalar * normal
                    velocities[i] += impulse / masses[i]
                    velocities[j] -= impulse / masses[j]

                    overlap = min_distance - distance
                    if overlap > 0:
                        total_mass = masses[i] + masses[j]
                        positions[i] -= normal * overlap * (masses[j] / total_mass)
                        positions[j] += normal * overlap * (masses[i] / total_mass)

                    if self.friction_enabled:
                        relative_velocity = velocities[i] - velocities[j]
                        v_normal_component = np.dot(relative_velocity, normal) * normal
                        tangential_velocity = relative_velocity - v_normal_component
                        tangential_speed = np.linalg.norm(tangential_velocity)
                        if tangential_speed > EPS:
                            tangent = tangential_velocity / tangential_speed
                            friction_coeff = (
                                self._friction_coeffs[ball_indices[i]]
                                + self._friction_coeffs[ball_indices[j]]
                            ) / 2.0
                            friction_scalar = friction_coeff * abs(impulse_scalar)
                            friction_impulse = friction_scalar * tangent
                            velocities[i] -= friction_impulse / masses[i]
                            velocities[j] += friction_impulse / masses[j]

        self._positions[ball_indices] = positions
        self._velocities[ball_indices] = velocities

    def _handle_ball_obstacle_collisions_vectorized(self) -> None:
        self._handle_ball_circle_obstacle_collisions_vectorized()
        self._handle_ball_rectangle_obstacle_collisions_vectorized()

    def _handle_ball_circle_obstacle_collisions_vectorized(self) -> None:
        n = self._n_entities
        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        circle_mask = self._is_static[:n] & (
            self._entity_types[:n] == EntityType.CIRCLE_OBSTACLE
        )
        ball_indices = np.where(ball_mask)[0]
        circle_indices = np.where(circle_mask)[0]
        if len(ball_indices) == 0 or len(circle_indices) == 0:
            return

        ball_positions = self._positions[ball_indices]
        ball_velocities = self._velocities[ball_indices]
        ball_radii = self._type_properties[EntityType.BALL]["radius"][ball_indices]
        ball_restitutions = self._restitutions[ball_indices]

        circle_positions = self._positions[circle_indices]
        circle_radii = self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][
            circle_indices
        ]

        for i, ball_idx in enumerate(ball_indices):
            for j, circle_idx in enumerate(circle_indices):
                delta = ball_positions[i] - circle_positions[j]
                distance = np.linalg.norm(delta)
                min_distance = ball_radii[i] + circle_radii[j]
                if distance < min_distance and distance > EPS:
                    normal = delta / distance
                    v_normal = np.dot(ball_velocities[i], normal)
                    if v_normal >= 0:
                        continue
                    ball_velocities[i] -= (
                        (1.0 + ball_restitutions[i]) * v_normal * normal
                    )
                    overlap = min_distance - distance
                    if overlap > 0:
                        ball_positions[i] += normal * overlap

                    if self.friction_enabled:
                        tangential_velocity = (
                            ball_velocities[i]
                            - np.dot(ball_velocities[i], normal) * normal
                        )
                        tangential_speed = np.linalg.norm(tangential_velocity)
                        if tangential_speed > EPS:
                            tangent = tangential_velocity / tangential_speed
                            friction_coeff = (
                                self._friction_coeffs[ball_idx]
                                + self._friction_coeffs[circle_idx]
                            ) / 2.0
                            normal_impulse = (1.0 + ball_restitutions[i]) * abs(
                                v_normal
                            )
                            friction_impulse = friction_coeff * normal_impulse * tangent
                            ball_velocities[i] -= friction_impulse

        self._positions[ball_indices] = ball_positions
        self._velocities[ball_indices] = ball_velocities

    def _handle_ball_rectangle_obstacle_collisions_vectorized(self) -> None:
        n = self._n_entities
        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        rect_mask = self._is_static[:n] & (
            self._entity_types[:n] == EntityType.RECTANGLE_OBSTACLE
        )
        ball_indices = np.where(ball_mask)[0]
        rect_indices = np.where(rect_mask)[0]
        if len(ball_indices) == 0 or len(rect_indices) == 0:
            return

        ball_positions = self._positions[ball_indices]
        ball_velocities = self._velocities[ball_indices]
        ball_radii = self._type_properties[EntityType.BALL]["radius"][ball_indices]
        ball_restitutions = self._restitutions[ball_indices]

        rect_positions = self._positions[rect_indices]
        rect_widths = self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][
            rect_indices
        ]
        rect_heights = self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][
            rect_indices
        ]

        for i, ball_idx in enumerate(ball_indices):
            for j, rect_idx in enumerate(rect_indices):
                rect_x = rect_positions[j][0]
                rect_y = rect_positions[j][1]
                half_width = rect_widths[j] / 2.0
                half_height = rect_heights[j] / 2.0

                rect_left = rect_x - half_width
                rect_right = rect_x + half_width
                rect_bottom = rect_y - half_height
                rect_top = rect_y + half_height

                ball_x = ball_positions[i][0]
                ball_y = ball_positions[i][1]

                closest_x = np.clip(ball_x, rect_left, rect_right)
                closest_y = np.clip(ball_y, rect_bottom, rect_top)

                delta_x = ball_x - closest_x
                delta_y = ball_y - closest_y
                distance = np.sqrt(delta_x**2 + delta_y**2)

                if distance < ball_radii[i]:
                    if distance < EPS:
                        dist_left = abs(ball_x - rect_left)
                        dist_right = abs(ball_x - rect_right)
                        dist_bottom = abs(ball_y - rect_bottom)
                        dist_top = abs(ball_y - rect_top)
                        min_dist = min(dist_left, dist_right, dist_bottom, dist_top)
                        if min_dist == dist_left:
                            normal = np.array([-1.0, 0.0])
                            overlap = ball_radii[i] + dist_left
                        elif min_dist == dist_right:
                            normal = np.array([1.0, 0.0])
                            overlap = ball_radii[i] + dist_right
                        elif min_dist == dist_bottom:
                            normal = np.array([0.0, -1.0])
                            overlap = ball_radii[i] + dist_bottom
                        else:
                            normal = np.array([0.0, 1.0])
                            overlap = ball_radii[i] + dist_top
                    else:
                        normal = np.array([delta_x / distance, delta_y / distance])
                        overlap = ball_radii[i] - distance

                    v_normal = np.dot(ball_velocities[i], normal)
                    if v_normal >= 0:
                        continue

                    ball_velocities[i] -= (
                        (1.0 + ball_restitutions[i]) * v_normal * normal
                    )
                    if overlap > 0:
                        ball_positions[i] += normal * overlap

                    if self.friction_enabled:
                        tangential_velocity = (
                            ball_velocities[i]
                            - np.dot(ball_velocities[i], normal) * normal
                        )
                        tangential_speed = np.linalg.norm(tangential_velocity)
                        if tangential_speed > EPS:
                            tangent = tangential_velocity / tangential_speed
                            friction_coeff = (
                                self._friction_coeffs[ball_idx]
                                + self._type_properties[EntityType.RECTANGLE_OBSTACLE][
                                    "friction_coefficient"
                                ][j]
                            ) / 2.0
                            normal_impulse = (1.0 + ball_restitutions[i]) * abs(
                                v_normal
                            )
                            friction_impulse = friction_coeff * normal_impulse * tangent
                            ball_velocities[i] -= friction_impulse

        self._positions[ball_indices] = ball_positions
        self._velocities[ball_indices] = ball_velocities
