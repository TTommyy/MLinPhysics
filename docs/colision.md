# Collision System

The physics engine implements comprehensive collision detection and response for multiple entity types.

---

# Algorithm (Brute Force - Element Wise)

Collision detection uses a complete element-wise comparison approach optimized with vectorization.

## Detection Strategy

- **Boundary Collisions**: Check each ball against 4 viewport boundaries
- **Ball-Ball Collisions**: Check all pairs (O(n²) complexity, optimized with upper triangle iteration)
- **Ball-Obstacle Collisions**: Check each ball against circle and rectangle obstacles separately

## Vectorization Optimization

- Processes multiple entities in single NumPy operations
- Filters dynamic entities before collision checks
- Caches entity data in local arrays for performance
- Supports 1000+ entities at 60 FPS

## Collision Response Sequence

1. **Collision Detection**: Distance calculation between entity boundaries
2. **Collision Normal**: Calculate surface normal at contact point
3. **Velocity Decomposition**: Separate normal and tangential components
4. **Impulse Resolution**: Apply collision response along normal
5. **Friction Application**: Apply tangential impulse if friction enabled
6. **Position Correction**: Separate overlapping bodies

---

# Restitution (Bounciness)

Restitution coefficient determines how much velocity is retained after collision.

Formula: **e = (v_separation) / (v_approach)**
- **e**: Coefficient of restitution (0-1)
- **v_separation**: Velocity magnitude after collision
- **v_approach**: Velocity magnitude before collision

## Behavior

- **e = 0**: Perfectly inelastic (no bounce, maximum energy loss)
- **e = 0.5**: Semi-elastic (moderate bounce)
- **e = 1.0**: Perfectly elastic (no energy loss, pure bounce)

## In Multi-Body Collisions

- **Ball-Ball**: Average restitution of both balls (e_avg = (e₁ + e₂) / 2)
- **Ball-Obstacle**: Uses ball's restitution coefficient
- **Boundary**: Uses ball's restitution coefficient

## Velocity Reflection

For collision normal **n** and relative velocity **v_rel**:

**v_after = v_before - (1 + e) * (v_rel · n) * n**

This preserves tangential velocity while damping normal component by factor (1 + e).

---

# Friction

Tangential damping at contact surface between entities.

## Friction Coefficient

- Range: 0.0 - 1.0
- **0.0**: Frictionless (no tangential resistance)
- **0.5**: Moderate friction
- **1.0**: Maximum friction (high tangential resistance)

## Behavior

- Acts perpendicular to collision normal
- Only applies if collision normal impulse exists
- Limited by normal impulse magnitude to prevent unrealistic effects

## Multi-Body Friction

- **Ball-Ball**: Average friction of both balls (f_avg = (f₁ + f₂) / 2)
- **Ball-Obstacle**: Average friction of ball and obstacle
- **Boundary**: Uses ball's friction coefficient

## Impulse Calculation

**f_impulse = friction_coeff * |normal_impulse| * tangent_direction**

Tangential impulse magnitude scales with normal collision strength.

---

# Collision Types

## Boundary Collisions

- Detect when ball radius extends past viewport boundary
- Separate ball back inside boundary
- Apply restitution to normal component of velocity
- Friction applies to tangential component

## Ball-Ball Collisions

- Detect center-to-center distance < sum of radii
- Calculate collision normal from centers
- Verify bodies are approaching (not separating)
- Apply impulse based on mass ratio (lighter body moves more)
- Position correction separates overlapping bodies proportionally to mass
- Friction applied along tangent

## Ball-Circle Obstacle Collisions

- Detect ball distance from obstacle center < (ball_radius + obstacle_radius)
- Collision normal points from obstacle to ball
- Static obstacle absorbs all impulse (ball reflects only)
- Friction affects only ball velocity

## Ball-Rectangle Obstacle Collisions

- Find closest point on rectangle perimeter to ball center
- Special case: Handle ball center inside rectangle (find nearest edge)
- Contact normal perpendicular to closest edge
- Static obstacle absorbs all impulse
- Friction affects only ball velocity


