import numpy as np

from .constants import EPS
from .types import EntityType


class CollisionMixin:
    def _resolve_with_pairs(self, pairs_by_type: dict[str, np.ndarray]) -> None:
        bb = pairs_by_type.get("ball_ball")
        if isinstance(bb, np.ndarray) and bb.size:
            self._resolve_ball_ball_pairs(bb)

        br = pairs_by_type.get("ball_rect")
        if isinstance(br, np.ndarray) and br.size:
            self._resolve_ball_rectangle_pairs(br)

        bc = pairs_by_type.get("ball_circle")
        if isinstance(bc, np.ndarray) and bc.size:
            self._resolve_ball_circle_pairs(bc)

    def _resolve_ball_ball_pairs(self, pairs: np.ndarray) -> None:
        i_idx = pairs[:, 0]
        j_idx = pairs[:, 1]
        pos_i = self._positions[i_idx]
        pos_j = self._positions[j_idx]
        vel_i = self._velocities[i_idx]
        vel_j = self._velocities[j_idx]
        m_i = self._masses[i_idx]
        m_j = self._masses[j_idx]
        r_i = self._type_properties[EntityType.BALL]["radius"][i_idx]
        r_j = self._type_properties[EntityType.BALL]["radius"][j_idx]
        e_i = self._restitutions[i_idx]
        e_j = self._restitutions[j_idx]

        delta = pos_j - pos_i
        dist = np.linalg.norm(delta, axis=1)
        min_dist = r_i + r_j
        collide = (dist < min_dist) & (dist > EPS)
        if not np.any(collide):
            return

        idx = np.where(collide)[0]
        nrm = delta[idx] / dist[idx][:, None]
        rel_v = vel_i[idx] - vel_j[idx]
        v_n = np.sum(rel_v * nrm, axis=1)
        # Mirror existing logic: skip if v_n <= 0
        mask = v_n > 0.0
        if not np.any(mask):
            # still resolve penetration to prevent sinking
            pen = min_dist[idx] - dist[idx]
            total_m = m_i[idx] + m_j[idx]
            corr = nrm * (pen[:, None] * (m_j[idx] / total_m)[:, None])
            np.add.at(self._positions, i_idx[idx], -corr)
            corr_j = nrm * (pen[:, None] * (m_i[idx] / total_m)[:, None])
            np.add.at(self._positions, j_idx[idx], corr_j)
            return

        sel = idx[mask]
        n = nrm[mask]
        rel = vel_i[sel] - vel_j[sel]
        vdot = np.sum(rel * n, axis=1)
        e = (e_i[sel] + e_j[sel]) * 0.5
        inv_mass = (1.0 / m_i[sel]) + (1.0 / m_j[sel])
        j_scalar = (-(1.0 + e) * vdot) / inv_mass
        imp = j_scalar[:, None] * n

        # Apply impulses
        np.add.at(self._velocities, i_idx[sel], imp / m_i[sel][:, None])
        np.add.at(self._velocities, j_idx[sel], -imp / m_j[sel][:, None])

        # Positional correction
        dist_sel = dist[sel]
        min_dist_sel = min_dist[sel]
        overlap = np.maximum(min_dist_sel - dist_sel, 0.0)
        if np.any(overlap > 0):
            tm = m_i[sel] + m_j[sel]
            corr_i = n * ((overlap * (m_j[sel] / tm))[:, None])
            corr_j = n * ((overlap * (m_i[sel] / tm))[:, None])
            np.add.at(self._positions, i_idx[sel], -corr_i)
            np.add.at(self._positions, j_idx[sel], corr_j)

        # Friction
        if getattr(self, "friction_enabled", False):
            rel = self._velocities[i_idx[sel]] - self._velocities[j_idx[sel]]
            v_n_comp = np.sum(rel * n, axis=1)[:, None] * n
            v_tan = rel - v_n_comp
            tan_norm = np.linalg.norm(v_tan, axis=1)
            t_mask = tan_norm > EPS
            if np.any(t_mask):
                t = v_tan[t_mask] / tan_norm[t_mask][:, None]
                mu = (
                    self._friction_coeffs[i_idx[sel][t_mask]]
                    + self._friction_coeffs[j_idx[sel][t_mask]]
                ) * 0.5
                f_imp = (mu * np.abs(j_scalar[t_mask]))[:, None] * t
                np.add.at(
                    self._velocities,
                    i_idx[sel][t_mask],
                    -f_imp / m_i[sel][t_mask][:, None],
                )
                np.add.at(
                    self._velocities,
                    j_idx[sel][t_mask],
                    f_imp / m_j[sel][t_mask][:, None],
                )

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

    def _resolve_ball_circle_pairs(self, pairs: np.ndarray) -> None:
        bi = pairs[:, 0]
        ci = pairs[:, 1]
        bp = self._positions[bi]
        bv = self._velocities[bi]
        br = self._type_properties[EntityType.BALL]["radius"][bi]
        be = self._restitutions[bi]

        cp = self._positions[ci]
        cr = self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][ci]

        delta = bp - cp
        dist = np.linalg.norm(delta, axis=1)
        min_dist = br + cr
        collide = (dist < min_dist) & (dist > EPS)
        if not np.any(collide):
            return
        idx = np.where(collide)[0]
        n = delta[idx] / dist[idx][:, None]
        v_n = np.sum(bv[idx] * n, axis=1)
        move_mask = v_n < 0.0
        if not np.any(move_mask):
            return
        sel = idx[move_mask]
        n_sel = n[move_mask]
        # Reflect velocity along normal with restitution
        jn = (1.0 + be[sel]) * v_n[move_mask]
        self._velocities[bi[sel]] -= jn[:, None] * n_sel

        # Positional correction
        overlap = min_dist[sel] - dist[sel]
        if np.any(overlap > 0):
            self._positions[bi[sel]] += n_sel * overlap[:, None]

        if getattr(self, "friction_enabled", False):
            tangential = self._velocities[bi[sel]] - (
                np.sum(self._velocities[bi[sel]] * n_sel, axis=1)[:, None] * n_sel
            )
            tan_speed = np.linalg.norm(tangential, axis=1)
            tmask = tan_speed > EPS
            if np.any(tmask):
                t = tangential[tmask] / tan_speed[tmask][:, None]
                mu = (
                    self._friction_coeffs[bi[sel][tmask]]
                    + self._friction_coeffs[ci[sel][tmask]]
                ) * 0.5
                normal_imp = (1.0 + be[sel][tmask]) * np.abs(v_n[move_mask][tmask])
                f_imp = (mu * normal_imp)[:, None] * t
                self._velocities[bi[sel][tmask]] -= f_imp

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

    def _resolve_ball_rectangle_pairs(self, pairs: np.ndarray) -> None:
        bi = pairs[:, 0]
        ri = pairs[:, 1]
        bp = self._positions[bi]
        bv = self._velocities[bi]
        br = self._type_properties[EntityType.BALL]["radius"][bi]
        be = self._restitutions[bi]

        rp = self._positions[ri]
        rw = self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][ri]
        rh = self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][ri]

        rect_left = rp[:, 0] - 0.5 * rw
        rect_right = rp[:, 0] + 0.5 * rw
        rect_bottom = rp[:, 1] - 0.5 * rh
        rect_top = rp[:, 1] + 0.5 * rh

        closest_x = np.clip(bp[:, 0], rect_left, rect_right)
        closest_y = np.clip(bp[:, 1], rect_bottom, rect_top)
        dx = bp[:, 0] - closest_x
        dy = bp[:, 1] - closest_y
        dist = np.sqrt(dx * dx + dy * dy)
        collide = dist < br
        if not np.any(collide):
            return

        idx = np.where(collide)[0]
        # normals for non-degenerate
        nz = dist[idx] > EPS
        normals = np.zeros((len(idx), 2), dtype=np.float64)
        normals[nz, 0] = dx[idx][nz] / dist[idx][nz]
        normals[nz, 1] = dy[idx][nz] / dist[idx][nz]

        # degenerate: choose nearest face normal
        dz = ~nz
        if np.any(dz):
            ii = idx[dz]
            dl = np.abs(bp[ii, 0] - rect_left[ii])
            dr = np.abs(bp[ii, 0] - rect_right[ii])
            db = np.abs(bp[ii, 1] - rect_bottom[ii])
            dt = np.abs(bp[ii, 1] - rect_top[ii])
            m = np.stack([dl, dr, db, dt], axis=1)
            arg = np.argmin(m, axis=1)
            # left,right,bottom,top
            normals_d = np.zeros((len(ii), 2), dtype=np.float64)
            normals_d[arg == 0] = np.array([-1.0, 0.0])
            normals_d[arg == 1] = np.array([1.0, 0.0])
            normals_d[arg == 2] = np.array([0.0, -1.0])
            normals_d[arg == 3] = np.array([0.0, 1.0])
            normals[dz] = normals_d

        v_n = np.sum(bv[idx] * normals, axis=1)
        move_mask = v_n < 0.0
        if not np.any(move_mask):
            return
        sel = idx[move_mask]
        n = normals[move_mask]
        self._velocities[bi[sel]] -= ((1.0 + be[sel]) * v_n[move_mask])[:, None] * n

        overlap = br[sel] - dist[sel]
        if np.any(overlap > 0):
            self._positions[bi[sel]] += n * overlap[:, None]

        if getattr(self, "friction_enabled", False):
            tangential = self._velocities[bi[sel]] - (
                np.sum(self._velocities[bi[sel]] * n, axis=1)[:, None] * n
            )
            tan_speed = np.linalg.norm(tangential, axis=1)
            tmask = tan_speed > EPS
            if np.any(tmask):
                t = tangential[tmask] / tan_speed[tmask][:, None]
                mu = (
                    self._friction_coeffs[bi[sel][tmask]]
                    + self._type_properties[EntityType.RECTANGLE_OBSTACLE][
                        "friction_coefficient"
                    ][ri[sel][tmask]]
                ) * 0.5
                normal_imp = (1.0 + be[sel][tmask]) * np.abs(v_n[move_mask][tmask])
                f_imp = (mu * normal_imp)[:, None] * t
                self._velocities[bi[sel][tmask]] -= f_imp
