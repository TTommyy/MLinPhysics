from enum import IntEnum

import numpy as np

from physics_sim.core import Entity, PhysicsEngine
from physics_sim.entities import Ball, CircleObstacle, RectangleObstacle


class EntityType(IntEnum):
    """Entity type enumeration for polymorphic storage."""

    BALL = 0
    RECTANGLE_OBSTACLE = 1
    CIRCLE_OBSTACLE = 2


class NumpyPhysicsEngine(PhysicsEngine):
    """High-performance physics engine using vectorized numpy operations.

    Uses Structure-of-Arrays (SoA) pattern for maximum performance:
    - All entity data stored in contiguous numpy arrays
    - Vectorized operations process all entities simultaneously
    - Entity objects are lightweight views into arrays
    - Supports multiple entity types (balls, obstacles)
    - Extensible to new entity types

    Performance target: 1000+ dynamic entities at 60 FPS
    """

    def __init__(self, bounds: tuple[float, float]):
        super().__init__(bounds)

        # Core arrays (all entities)
        self._n_entities: int = 0
        self._capacity: int = 16  # Initial capacity, grows as needed

        # Shared properties for all entities
        self._positions: np.ndarray = np.zeros((self._capacity, 2), dtype=np.float64)
        self._entity_types: np.ndarray = np.zeros(self._capacity, dtype=np.int32)
        self._is_static: np.ndarray = np.zeros(self._capacity, dtype=bool)

        # Dynamic entity properties (used for all entities, but 0 for static)
        self._dynamic_mask: np.ndarray = np.zeros(self._capacity, dtype=bool)
        self._velocities: np.ndarray = np.zeros((self._capacity, 2), dtype=np.float64)
        self._accelerations: np.ndarray = np.zeros(
            (self._capacity, 2), dtype=np.float64
        )
        self._masses: np.ndarray = np.zeros(self._capacity, dtype=np.float64)
        self._restitutions: np.ndarray = np.zeros(self._capacity, dtype=np.float64)
        self._drag_coeffs: np.ndarray = np.zeros(self._capacity, dtype=np.float64)
        self._cross_sections: np.ndarray = np.zeros(self._capacity, dtype=np.float64)

        # Type-specific properties (parallel arrays indexed by entity index)
        self._type_properties: dict[EntityType, dict] = {
            EntityType.BALL: {
                "radius": np.zeros(self._capacity, dtype=np.float64),
                "color": [None] * self._capacity,
            },
            EntityType.RECTANGLE_OBSTACLE: {
                "width": np.zeros(self._capacity, dtype=np.float64),
                "height": np.zeros(self._capacity, dtype=np.float64),
                "color": [None] * self._capacity,
            },
            EntityType.CIRCLE_OBSTACLE: {
                "radius": np.zeros(self._capacity, dtype=np.float64),
                "color": [None] * self._capacity,
            },
        }

        # Entity ID tracking
        self._entity_ids: list[str] = [None] * self._capacity
        self._id_to_index: dict[str, int] = {}

        # Force tracking (per entity, for UI display)
        self._applied_forces: list[list[tuple[str, np.ndarray]]] = [
            [] for _ in range(self._capacity)
        ]

        # Pause state
        self._paused: bool = False

    def _grow_arrays(self, min_additional: int = 1):
        """Grow all arrays to accommodate more entities."""
        new_capacity = max(self._capacity * 2, self._capacity + min_additional)

        # Grow shared arrays
        self._positions = np.resize(self._positions, (new_capacity, 2))
        self._entity_types = np.resize(self._entity_types, new_capacity)
        self._is_static = np.resize(self._is_static, new_capacity)

        # Grow dynamic arrays
        self._dynamic_mask = np.resize(self._dynamic_mask, new_capacity)
        self._velocities = np.resize(self._velocities, (new_capacity, 2))
        self._accelerations = np.resize(self._accelerations, (new_capacity, 2))
        self._masses = np.resize(self._masses, new_capacity)
        self._restitutions = np.resize(self._restitutions, new_capacity)
        self._drag_coeffs = np.resize(self._drag_coeffs, new_capacity)
        self._cross_sections = np.resize(self._cross_sections, new_capacity)

        # Grow type-specific arrays
        for _, props in self._type_properties.items():
            for key, arr in props.items():
                if isinstance(arr, np.ndarray):
                    props[key] = np.resize(arr, new_capacity)
                elif isinstance(arr, list):
                    props[key].extend([None] * (new_capacity - self._capacity))

        # Grow ID and force tracking arrays
        self._entity_ids.extend([None] * (new_capacity - self._capacity))
        self._applied_forces.extend([[] for _ in range(new_capacity - self._capacity)])

        self._capacity = new_capacity

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the simulation by extracting data to arrays.

        The entity object is used only for data extraction and then discarded.
        This maintains the SoA (Structure-of-Arrays) pattern for performance.

        Args:
            entity: Entity object (will not be stored, only data extracted)
        """
        # Check if we need to grow arrays
        if self._n_entities >= self._capacity:
            self._grow_arrays()

        idx = self._n_entities
        entity_id = entity.id

        # Determine entity type and populate arrays
        if isinstance(entity, Ball):
            self._add_ball(entity, idx)
        elif isinstance(entity, RectangleObstacle):
            self._add_rectangle_obstacle(entity, idx)
        elif isinstance(entity, CircleObstacle):
            self._add_circle_obstacle(entity, idx)
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")

        # Store ID and create mapping (entity object is discarded)
        self._entity_ids[idx] = entity_id
        self._id_to_index[entity_id] = idx
        self._n_entities += 1

    def _add_ball(self, ball: Ball, idx: int):
        """Add a Ball entity to arrays."""
        self._positions[idx] = ball.position
        self._entity_types[idx] = EntityType.BALL
        self._is_static[idx] = False
        self._dynamic_mask[idx] = True

        # Dynamic properties
        self._velocities[idx] = ball.velocity
        self._masses[idx] = ball.mass
        self._restitutions[idx] = ball.restitution
        self._drag_coeffs[idx] = ball.drag_coefficient
        self._cross_sections[idx] = ball.cross_sectional_area

        # Ball-specific properties
        self._type_properties[EntityType.BALL]["radius"][idx] = ball.radius
        self._type_properties[EntityType.BALL]["color"][idx] = ball.color

    def _add_rectangle_obstacle(self, obstacle, idx: int):
        """Add a RectangleObstacle entity to arrays."""
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

        # Rectangle-specific properties
        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["width"][idx] = (
            obstacle.width
        )
        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["height"][idx] = (
            obstacle.height
        )
        self._type_properties[EntityType.RECTANGLE_OBSTACLE]["color"][idx] = (
            obstacle.color
        )

    def _add_circle_obstacle(self, obstacle, idx: int):
        """Add a CircleObstacle entity to arrays."""
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

        # Circle obstacle-specific properties
        self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][idx] = (
            obstacle.radius
        )
        self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][idx] = obstacle.color

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from the simulation."""
        if entity_id not in self._id_to_index:
            return

        idx = self._id_to_index[entity_id]

        # Swap with last entity and decrement count
        last_idx = self._n_entities - 1
        if idx != last_idx:
            # Copy last entity data to removed position
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

            # Copy type-specific properties
            for entity_type, props in self._type_properties.items():
                for key, arr in props.items():
                    if isinstance(arr, np.ndarray):
                        arr[idx] = arr[last_idx]
                    elif isinstance(arr, list):
                        arr[idx] = arr[last_idx]

            # Update ID and mapping
            self._entity_ids[idx] = self._entity_ids[last_idx]
            self._id_to_index[self._entity_ids[idx]] = idx
            self._applied_forces[idx] = self._applied_forces[last_idx]

        # Remove last entity
        del self._id_to_index[entity_id]
        self._n_entities -= 1

    def clear(self) -> None:
        """Remove all entities from the simulation."""
        self._n_entities = 0
        self._id_to_index.clear()

    def step(self, dt: float) -> None:
        """Advance simulation using vectorized Euler integration."""
        if self._paused or self._n_entities == 0:
            return

        # Get active slice
        n = self._n_entities

        # Get dynamic entity mask
        dyn = self._dynamic_mask[:n]
        n_dynamic = dyn.sum()

        if n_dynamic == 0:
            return

        # Reset accelerations for dynamic entities (vectorized)
        self._accelerations[:n][dyn] = 0.0

        # Clear force tracking for all entities
        for i in range(n):
            self._applied_forces[i].clear()

        # Apply all forces (vectorized batch operations)
        for force in self.forces:
            # Get force vectors for all dynamic entities
            force_vectors = force.apply_to_batch(
                positions=self._positions[:n][dyn],
                velocities=self._velocities[:n][dyn],
                masses=self._masses[:n][dyn],
                drag_coeffs=self._drag_coeffs[:n][dyn],
                cross_sections=self._cross_sections[:n][dyn],
                entity_types=self._entity_types[:n][dyn],
                dt=dt,
            )

            # Apply forces: a = F/m (vectorized)
            masses_reshaped = self._masses[:n][dyn][:, np.newaxis]
            self._accelerations[:n][dyn] += force_vectors / masses_reshaped

            # Track forces for entities (for UI display)
            dyn_indices = np.where(dyn)[0]
            for i, entity_idx in enumerate(dyn_indices):
                self._applied_forces[entity_idx].append((force.name, force_vectors[i]))

        # Euler integration (vectorized, dynamic only)
        self._velocities[:n][dyn] += self._accelerations[:n][dyn] * dt
        self._positions[:n][dyn] += self._velocities[:n][dyn] * dt

        # Boundary collisions (vectorized)
        self._handle_boundary_collisions_vectorized()

        # Entity-entity collisions (vectorized)
        self._handle_ball_ball_collisions_vectorized()
        self._handle_ball_obstacle_collisions_vectorized()

    def _handle_boundary_collisions_vectorized(self) -> None:
        """Vectorized boundary collision detection and response."""
        width, height = self.bounds
        n = self._n_entities

        # Only handle balls (dynamic and type==BALL)
        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        ball_indices = np.where(ball_mask)[0]

        if len(ball_indices) == 0:
            return

        radii = self._type_properties[EntityType.BALL]["radius"][ball_indices]

        # Left boundary
        left_collision = self._positions[ball_indices, 0] - radii < 0
        if left_collision.any():
            self._positions[ball_indices[left_collision], 0] = radii[left_collision]
            self._velocities[ball_indices[left_collision], 0] *= -self._restitutions[
                ball_indices[left_collision]
            ]

        # Right boundary
        right_collision = self._positions[ball_indices, 0] + radii > width
        if right_collision.any():
            self._positions[ball_indices[right_collision], 0] = (
                width - radii[right_collision]
            )
            self._velocities[ball_indices[right_collision], 0] *= -self._restitutions[
                ball_indices[right_collision]
            ]

        # Bottom boundary
        bottom_collision = self._positions[ball_indices, 1] - radii < 0
        if bottom_collision.any():
            self._positions[ball_indices[bottom_collision], 1] = radii[bottom_collision]
            self._velocities[ball_indices[bottom_collision], 1] *= -self._restitutions[
                ball_indices[bottom_collision]
            ]

        # Top boundary
        top_collision = self._positions[ball_indices, 1] + radii > height
        if top_collision.any():
            self._positions[ball_indices[top_collision], 1] = (
                height - radii[top_collision]
            )
            self._velocities[ball_indices[top_collision], 1] *= -self._restitutions[
                ball_indices[top_collision]
            ]

    def _handle_ball_ball_collisions_vectorized(self) -> None:
        """Vectorized ball-ball collision detection and elastic response."""
        n = self._n_entities

        # Get ball mask and indices
        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        ball_indices = np.where(ball_mask)[0]

        if len(ball_indices) < 2:
            return

        # Cache ball data for performance
        positions = self._positions[ball_indices]
        velocities = self._velocities[ball_indices]
        masses = self._masses[ball_indices]
        radii = self._type_properties[EntityType.BALL]["radius"][ball_indices]
        restitutions = self._restitutions[ball_indices]

        n_balls = len(ball_indices)

        # Check all pairs (upper triangle to avoid duplicate checks)
        for i in range(n_balls):
            for j in range(i + 1, n_balls):
                # Calculate distance vector
                delta = positions[j] - positions[i]
                distance = np.linalg.norm(delta)

                # Check for collision
                min_distance = radii[i] + radii[j]
                if distance < min_distance and distance > 1e-10:
                    # Collision normal (from i to j)
                    normal = delta / distance

                    # Relative velocity
                    relative_velocity = velocities[i] - velocities[j]

                    # Velocity along normal
                    v_normal = np.dot(relative_velocity, normal)

                    # Don't resolve if objects are separating
                    if v_normal <= 0:
                        continue

                    # Calculate restitution (average of both balls)
                    restitution = (restitutions[i] + restitutions[j]) / 2.0

                    # Calculate impulse scalar using momentum conservation
                    # j = -(1 + e) * v_rel · n / (1/m1 + 1/m2)
                    impulse_scalar = (
                        -(1.0 + restitution)
                        * v_normal
                        / (1.0 / masses[i] + 1.0 / masses[j])
                    )

                    # Apply impulse to velocities
                    impulse = impulse_scalar * normal
                    velocities[i] += impulse / masses[i]
                    velocities[j] -= impulse / masses[j]

                    # Position correction (separate overlapping balls)
                    overlap = min_distance - distance
                    if overlap > 0:
                        # Separate proportionally to masses (lighter moves more)
                        total_mass = masses[i] + masses[j]
                        correction_i = -normal * overlap * (masses[j] / total_mass)
                        correction_j = normal * overlap * (masses[i] / total_mass)

                        positions[i] += correction_i
                        positions[j] += correction_j

        # Write back updated values
        self._positions[ball_indices] = positions
        self._velocities[ball_indices] = velocities

    def _handle_ball_obstacle_collisions_vectorized(self) -> None:
        """Dispatcher for ball-obstacle collisions."""
        self._handle_ball_circle_obstacle_collisions_vectorized()
        self._handle_ball_rectangle_obstacle_collisions_vectorized()

    def _handle_ball_circle_obstacle_collisions_vectorized(self) -> None:
        """Vectorized ball-circle obstacle collision detection and response."""
        n = self._n_entities

        # Get ball and circle obstacle indices
        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        circle_mask = self._is_static[:n] & (
            self._entity_types[:n] == EntityType.CIRCLE_OBSTACLE
        )

        ball_indices = np.where(ball_mask)[0]
        circle_indices = np.where(circle_mask)[0]

        if len(ball_indices) == 0 or len(circle_indices) == 0:
            return

        # Cache data
        ball_positions = self._positions[ball_indices]
        ball_velocities = self._velocities[ball_indices]
        ball_radii = self._type_properties[EntityType.BALL]["radius"][ball_indices]
        ball_restitutions = self._restitutions[ball_indices]

        circle_positions = self._positions[circle_indices]
        circle_radii = self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][
            circle_indices
        ]

        # Check all ball-circle pairs
        for i, ball_idx in enumerate(ball_indices):
            for j, circle_idx in enumerate(circle_indices):
                # Calculate distance vector
                delta = ball_positions[i] - circle_positions[j]
                distance = np.linalg.norm(delta)

                # Check for collision
                min_distance = ball_radii[i] + circle_radii[j]
                if distance < min_distance and distance > 1e-10:
                    # Collision normal (from circle to ball)
                    normal = delta / distance

                    # Velocity along normal
                    v_normal = np.dot(ball_velocities[i], normal)

                    # Only resolve if ball is moving into obstacle
                    if v_normal >= 0:
                        continue

                    # Reflect velocity with restitution
                    ball_velocities[i] -= (
                        (1.0 + ball_restitutions[i]) * v_normal * normal
                    )

                    # Position correction (push ball out of obstacle)
                    overlap = min_distance - distance
                    if overlap > 0:
                        ball_positions[i] += normal * overlap

        # Write back updated values
        self._positions[ball_indices] = ball_positions
        self._velocities[ball_indices] = ball_velocities

    def _handle_ball_rectangle_obstacle_collisions_vectorized(self) -> None:
        """Vectorized ball-rectangle obstacle collision detection and response."""
        n = self._n_entities

        # Get ball and rectangle obstacle indices
        ball_mask = self._dynamic_mask[:n] & (self._entity_types[:n] == EntityType.BALL)
        rect_mask = self._is_static[:n] & (
            self._entity_types[:n] == EntityType.RECTANGLE_OBSTACLE
        )

        ball_indices = np.where(ball_mask)[0]
        rect_indices = np.where(rect_mask)[0]

        if len(ball_indices) == 0 or len(rect_indices) == 0:
            return

        # Cache data
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

        # Check all ball-rectangle pairs
        for i, ball_idx in enumerate(ball_indices):
            for j, rect_idx in enumerate(rect_indices):
                # Rectangle bounds (assuming position is center)
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

                # Find closest point on rectangle to ball center
                closest_x = np.clip(ball_x, rect_left, rect_right)
                closest_y = np.clip(ball_y, rect_bottom, rect_top)

                # Calculate distance from ball center to closest point
                delta_x = ball_x - closest_x
                delta_y = ball_y - closest_y
                distance = np.sqrt(delta_x**2 + delta_y**2)

                # Check for collision
                if distance < ball_radii[i]:
                    # Handle case when ball center is inside rectangle
                    if distance < 1e-10:
                        # Find which edge is closest
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
                        else:  # top
                            normal = np.array([0.0, 1.0])
                            overlap = ball_radii[i] + dist_top
                    else:
                        # Normal from closest point to ball center
                        normal = np.array([delta_x / distance, delta_y / distance])
                        overlap = ball_radii[i] - distance

                    # Velocity along normal
                    v_normal = np.dot(ball_velocities[i], normal)

                    # Only resolve if ball is moving into obstacle
                    if v_normal >= 0:
                        continue

                    # Reflect velocity with restitution
                    ball_velocities[i] -= (
                        (1.0 + ball_restitutions[i]) * v_normal * normal
                    )

                    # Position correction (push ball out of obstacle)
                    if overlap > 0:
                        ball_positions[i] += normal * overlap

        # Write back updated values
        self._positions[ball_indices] = ball_positions
        self._velocities[ball_indices] = ball_velocities

    def pause(self) -> None:
        """Pause the physics simulation."""
        self._paused = True

    def is_paused(self) -> bool:
        """Check if physics simulation is paused."""
        return self._paused

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self._paused = not self._paused

    def get_supported_entity_types(self) -> list[type]:
        """Return list of entity classes supported by NumpyPhysicsEngine."""
        from physics_sim.entities import Ball, CircleObstacle, RectangleObstacle

        return [Ball, RectangleObstacle, CircleObstacle]

    def get_render_data(self) -> list[dict]:
        """Return rendering data directly from arrays."""
        render_data = []

        for i in range(self._n_entities):
            entity_type = EntityType(self._entity_types[i])

            base_data = {
                "id": self._entity_ids[i],
                "type": entity_type.name,
                "position": tuple(self._positions[i]),
            }

            # Add type-specific properties
            if entity_type == EntityType.BALL:
                base_data.update({
                    "render_type": "circle",
                    "radius": float(
                        self._type_properties[EntityType.BALL]["radius"][i]
                    ),
                    "color": self._type_properties[EntityType.BALL]["color"][i],
                })
            elif entity_type == EntityType.RECTANGLE_OBSTACLE:
                base_data.update({
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
                base_data.update({
                    "render_type": "circle_static",
                    "radius": float(
                        self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][i]
                    ),
                    "color": self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][
                        i
                    ],
                })

            render_data.append(base_data)

        return render_data

    def get_inventory_data(self) -> list[dict]:
        """Return full physics data for UI panels."""
        inventory_data = []

        for i in range(self._n_entities):
            if not self._dynamic_mask[i]:
                continue  # Skip static entities in inventory

            entity_type = EntityType(self._entity_types[i])

            data = {
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

            # Add type-specific data
            if entity_type == EntityType.BALL:
                data["radius"] = float(
                    self._type_properties[EntityType.BALL]["radius"][i]
                )
                data["restitution"] = float(self._restitutions[i])

            inventory_data.append(data)

        return inventory_data

    def get_entity_for_editing(self, entity_id: str) -> Entity | None:
        """Create temporary entity object from array data."""
        if entity_id not in self._id_to_index:
            return None

        idx = self._id_to_index[entity_id]
        entity_type = EntityType(self._entity_types[idx])

        # Recreate entity object from array data
        if entity_type == EntityType.BALL:
            return Ball(
                position=self._positions[idx].copy(),
                velocity=self._velocities[idx].copy(),
                radius=float(self._type_properties[EntityType.BALL]["radius"][idx]),
                mass=float(self._masses[idx]),
                color=self._type_properties[EntityType.BALL]["color"][idx],
                restitution=float(self._restitutions[idx]),
                drag_coefficient=float(self._drag_coeffs[idx]),
                entity_id=entity_id,
            )
        elif entity_type == EntityType.RECTANGLE_OBSTACLE:
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
                entity_id=entity_id,
            )
        elif entity_type == EntityType.CIRCLE_OBSTACLE:
            return CircleObstacle(
                position=self._positions[idx].copy(),
                radius=float(
                    self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][idx]
                ),
                color=self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][idx],
                entity_id=entity_id,
            )

        return None

    def update_entity_from_object(self, entity: Entity) -> bool:
        """Update arrays from modified entity object."""
        if entity.id not in self._id_to_index:
            return False

        idx = self._id_to_index[entity.id]

        # Update arrays from entity object
        if isinstance(entity, Ball):
            self._positions[idx] = entity.position
            self._velocities[idx] = entity.velocity
            self._masses[idx] = entity.mass
            self._restitutions[idx] = entity.restitution
            self._drag_coeffs[idx] = entity.drag_coefficient
            self._cross_sections[idx] = entity.cross_sectional_area
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
        elif isinstance(entity, CircleObstacle):
            self._positions[idx] = entity.position
            self._type_properties[EntityType.CIRCLE_OBSTACLE]["radius"][idx] = (
                entity.radius
            )
            self._type_properties[EntityType.CIRCLE_OBSTACLE]["color"][idx] = (
                entity.color
            )
        else:
            return False

        return True

    # Internal array access for entity views
    def _get_position(self, idx: int) -> np.ndarray:
        """Get position array view for entity at index."""
        return self._positions[idx]

    def _get_velocity(self, idx: int) -> np.ndarray:
        """Get velocity array view for entity at index."""
        return self._velocities[idx]

    def _get_mass(self, idx: int) -> float:
        """Get mass for entity at index."""
        return float(self._masses[idx])

    def _set_mass(self, idx: int, value: float):
        """Set mass for entity at index."""
        self._masses[idx] = value

    def get_energies(self) -> dict[str, float]:
        """Calculate total kinetic and potential energy in the system.

        Returns:
            Dictionary with kinetic, potential, and total energy
        """
        if self._n_entities == 0:
            return {"kinetic": 0.0, "potential": 0.0, "total": 0.0}

        n = self._n_entities
        dyn = self._dynamic_mask[:n]

        # Kinetic energy: KE = 0.5 * m * v²
        velocities_sq = np.sum(self._velocities[:n][dyn] ** 2, axis=1)
        kinetic_energy = float(0.5 * np.sum(self._masses[:n][dyn] * velocities_sq))

        # Potential energy: Sum contributions from all forces
        potential_energy = 0.0
        for force in self.forces:
            pe_contribution = force.get_potential_energy_contribution(
                positions=self._positions[:n][dyn],
                masses=self._masses[:n][dyn],
            )
            potential_energy += pe_contribution

        total_energy = kinetic_energy + potential_energy

        return {
            "kinetic": kinetic_energy,
            "potential": potential_energy,
            "total": total_energy,
        }

    def get_entity_counts_by_type(self) -> dict[str, int]:
        """Get count of entities by type.

        Returns:
            Dictionary mapping entity type names to counts
        """
        counts = {}
        for i in range(self._n_entities):
            entity_type = EntityType(self._entity_types[i])
            type_name = entity_type.name
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
