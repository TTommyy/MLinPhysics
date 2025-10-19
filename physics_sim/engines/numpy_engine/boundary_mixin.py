import numpy as np
from .types import EntityType


class BoundaryMixin:
    def _handle_boundary_collisions_vectorized(self) -> None:
        width, height = self.bounds
        n = self._n_entities

        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        ball_indices = np.where(ball_mask)[0]
        if len(ball_indices) == 0:
            return

        radii = self._type_properties[EntityType.BALL]["radius"][ball_indices]

        left_collision = self._positions[ball_indices, 0] - radii < 0
        if left_collision.any():
            self._positions[ball_indices[left_collision], 0] = radii[left_collision]
            self._velocities[ball_indices[left_collision], 0] *= -self._restitutions[
                ball_indices[left_collision]
            ]

        right_collision = self._positions[ball_indices, 0] + radii > width
        if right_collision.any():
            self._positions[ball_indices[right_collision], 0] = (
                width - radii[right_collision]
            )
            self._velocities[ball_indices[right_collision], 0] *= -self._restitutions[
                ball_indices[right_collision]
            ]

        bottom_collision = self._positions[ball_indices, 1] - radii < 0
        if bottom_collision.any():
            self._positions[ball_indices[bottom_collision], 1] = radii[bottom_collision]
            self._velocities[ball_indices[bottom_collision], 1] *= -self._restitutions[
                ball_indices[bottom_collision]
            ]

        top_collision = self._positions[ball_indices, 1] + radii > height
        if top_collision.any():
            self._positions[ball_indices[top_collision], 1] = (
                height - radii[top_collision]
            )
            self._velocities[ball_indices[top_collision], 1] *= -self._restitutions[
                ball_indices[top_collision]
            ]
