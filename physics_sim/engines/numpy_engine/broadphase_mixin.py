from __future__ import annotations

from typing import Protocol

import numpy as np
from numba import njit

from .bvh import build_lbvh, enumerate_overlapping_pairs
from .types import EntityType


class BroadphaseMixinAttrs(Protocol):
    _n_entities: int
    _positions: np.ndarray
    _entity_types: np.ndarray
    _dynamic_mask: np.ndarray
    _type_properties: dict[EntityType, dict[str, np.ndarray]]
    bounds: tuple[float, float]


class BroadphaseMixin(BroadphaseMixinAttrs):
    def _compute_aabbs_for_colliders(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = self._n_entities
        if n == 0:
            return (
                np.empty((0, self._positions.shape[1]), dtype=np.float64),
                np.empty((0, self._positions.shape[1]), dtype=np.float64),
                np.empty((0,), dtype=np.int32),
            )

        d = self._positions.shape[1]
        et = self._entity_types[:n]

        is_ball = et == EntityType.BALL
        is_rect = et == EntityType.RECTANGLE_OBSTACLE
        is_circle = et == EntityType.CIRCLE_OBSTACLE

        collider_mask = is_ball | is_rect | is_circle
        indices = np.where(collider_mask)[0].astype(np.int32)
        if len(indices) == 0:
            return (
                np.empty((0, d), dtype=np.float64),
                np.empty((0, d), dtype=np.float64),
                np.empty((0,), dtype=np.int32),
            )

        pos = self._positions[indices]

        aabb_min = np.zeros((len(indices), d), dtype=np.float64)
        aabb_max = np.zeros((len(indices), d), dtype=np.float64)

        # BALL: use optimized kernel
        if is_ball.any():
            ball_local = np.where(is_ball[indices])[0]
            if len(ball_local) > 0:
                ball_idx = indices[ball_local]
                r = self._type_properties[EntityType.BALL]["radius"][ball_idx]
                min_b, max_b = _compute_spherical_aabbs(pos[ball_local], r, d)
                aabb_min[ball_local] = min_b
                aabb_max[ball_local] = max_b

        # CIRCLE_OBSTACLE: use optimized kernel
        if is_circle.any():
            circ_local = np.where(is_circle[indices])[0]
            if len(circ_local) > 0:
                circ_idx = indices[circ_local]
                r = self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][
                    circ_idx
                ]
                min_c, max_c = _compute_spherical_aabbs(pos[circ_local], r, d)
                aabb_min[circ_local] = min_c
                aabb_max[circ_local] = max_c

        # RECTANGLE_OBSTACLE: use optimized kernel
        if is_rect.any():
            rect_local = np.where(is_rect[indices])[0]
            if len(rect_local) > 0:
                rect_idx = indices[rect_local]
                w = self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][
                    rect_idx
                ]
                h = self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][
                    rect_idx
                ]
                min_r, max_r = _compute_rectangle_aabbs(pos[rect_local], w, h, d)
                aabb_min[rect_local] = min_r
                aabb_max[rect_local] = max_r

        return aabb_min, aabb_max, indices

    def _build_bvh_and_pairs(self) -> dict[str, np.ndarray]:
        aabb_min, aabb_max, collider_indices = self._compute_aabbs_for_colliders()  # type: ignore
        if aabb_min.shape[0] == 0:
            return {
                "ball_ball": np.empty((0, 2), dtype=np.int32),
                "ball_rect": np.empty((0, 2), dtype=np.int32),
                "ball_circle": np.empty((0, 2), dtype=np.int32),
            }

        d = aabb_min.shape[1]
        bounds_min = np.zeros((d,), dtype=np.float64)
        bounds_max = np.zeros((d,), dtype=np.float64)
        # Use engine bounds for first two dims, zeros elsewhere
        bounds_max[: min(2, d)] = np.asarray(self.bounds, dtype=np.float64)[: min(2, d)]

        bvh, _ = build_lbvh(aabb_min, aabb_max, bounds_min, bounds_max)
        all_pairs = enumerate_overlapping_pairs(bvh)  # indices in collider space
        if all_pairs.shape[0] == 0:
            return {
                "ball_ball": np.empty((0, 2), dtype=np.int32),
                "ball_rect": np.empty((0, 2), dtype=np.int32),
                "ball_circle": np.empty((0, 2), dtype=np.int32),
            }

        # Map pairs from collider space back to engine space
        a = collider_indices[all_pairs[:, 0]]
        b = collider_indices[all_pairs[:, 1]]

        et = self._entity_types
        dyn = self._dynamic_mask

        type_a = et[a]
        type_b = et[b]

        # ball-ball: both balls, at least one dynamic
        bb_mask = (
            (type_a == EntityType.BALL)
            & (type_b == EntityType.BALL)
            & (dyn[a] | dyn[b])
        )
        ball_ball = all_pairs[bb_mask]

        # ball-rect: reorder so ball is first; require ball dynamic
        br_mask1 = (
            (type_a == EntityType.BALL)
            & (type_b == EntityType.RECTANGLE_OBSTACLE)
            & dyn[a]
        )
        br_mask2 = (
            (type_b == EntityType.BALL)
            & (type_a == EntityType.RECTANGLE_OBSTACLE)
            & dyn[b]
        )
        br_pairs = []
        if np.any(br_mask1):
            br_pairs.append(all_pairs[br_mask1])
        if np.any(br_mask2):
            swapped = np.stack(
                [all_pairs[br_mask2][:, 1], all_pairs[br_mask2][:, 0]], axis=1
            )
            br_pairs.append(swapped)
        ball_rect = (
            np.concatenate(br_pairs, axis=0)
            if br_pairs
            else np.empty((0, 2), dtype=np.int32)
        )

        # ball-circle: reorder so ball is first; require ball dynamic
        bc_mask1 = (
            (type_a == EntityType.BALL)
            & (type_b == EntityType.CIRCLE_OBSTACLE)
            & dyn[a]
        )
        bc_mask2 = (
            (type_b == EntityType.BALL)
            & (type_a == EntityType.CIRCLE_OBSTACLE)
            & dyn[b]
        )
        bc_pairs = []
        if np.any(bc_mask1):
            bc_pairs.append(all_pairs[bc_mask1])
        if np.any(bc_mask2):
            swapped = np.stack(
                [all_pairs[bc_mask2][:, 1], all_pairs[bc_mask2][:, 0]], axis=1
            )
            bc_pairs.append(swapped)
        ball_circle = (
            np.concatenate(bc_pairs, axis=0)
            if bc_pairs
            else np.empty((0, 2), dtype=np.int32)
        )

        return {
            "ball_ball": ball_ball.astype(np.int32),
            "ball_rect": ball_rect.astype(np.int32),
            "ball_circle": ball_circle.astype(np.int32),
        }


@njit(cache=True, fastmath=True)
def _compute_spherical_aabbs(
    positions: np.ndarray, radii: np.ndarray, d: int
) -> tuple[np.ndarray, np.ndarray]:
    """Compute AABBs for spherical entities (balls, circles)."""
    n = len(positions)
    aabb_min = np.empty((n, d), dtype=np.float64)
    aabb_max = np.empty((n, d), dtype=np.float64)

    for i in range(n):
        for dim in range(d):
            aabb_min[i, dim] = positions[i, dim] - radii[i]
            aabb_max[i, dim] = positions[i, dim] + radii[i]

    return aabb_min, aabb_max


@njit(cache=True, fastmath=True)
def _compute_rectangle_aabbs(
    positions: np.ndarray, widths: np.ndarray, heights: np.ndarray, d: int
) -> tuple[np.ndarray, np.ndarray]:
    """Compute AABBs for rectangular entities."""
    n = len(positions)
    aabb_min = np.empty((n, d), dtype=np.float64)
    aabb_max = np.empty((n, d), dtype=np.float64)

    for i in range(n):
        half_w = 0.5 * widths[i]
        half_h = 0.5 * heights[i]

        aabb_min[i, 0] = positions[i, 0] - half_w
        aabb_max[i, 0] = positions[i, 0] + half_w

        if d > 1:
            aabb_min[i, 1] = positions[i, 1] - half_h
            aabb_max[i, 1] = positions[i, 1] + half_h

        # Handle additional dimensions if present
        for dim in range(2, d):
            aabb_min[i, dim] = positions[i, dim]
            aabb_max[i, dim] = positions[i, dim]

    return aabb_min, aabb_max
