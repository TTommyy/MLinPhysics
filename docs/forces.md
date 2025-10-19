# LinearGravity

Global gravitational force that applies constant acceleration to all dynamic entities.

Formula: **F = m * g**
- **F**: Force vector (N)
- **m**: Entity mass (kg)
- **g**: Gravitational acceleration vector (m/s²)

## Parameters

- **Acceleration [x, y]**: Direction and magnitude of gravitational force
  - Default: [0.0, -9.81] (downward acceleration matching Earth gravity)
  - Affects all dynamic entities uniformly regardless of mass

## Behavior

- Applies instantaneously to all entities each simulation step
- Direction and magnitude are fully customizable (allows for sideways or upward gravity)
- Linear relationship with mass (heavier objects experience proportionally greater force)
- Contributes to potential energy calculation based on vertical position

## Potential Energy

PE = m * g * h

Where h is height (y-coordinate). Higher positions accumulate more gravitational potential energy.

---

# Drag

Air resistance / fluid resistance force opposing entity motion.

Formula: **F_D = -(1/2) * ρ * v² * C_D * A * (v/|v|)**
- **F_D**: Drag force (N)
- **ρ**: Fluid density (kg/m³)
- **v**: Velocity vector (m/s)
- **C_D**: Drag coefficient (unitless, ~0.47 for spheres)
- **A**: Cross-sectional area (m²)

## Parameters

- **Fluid Density**: Density of the fluid entities move through
  - Default: 1.225 kg/m³ (air at sea level)
  - Range: 0.1 - 10.0

- **Linear Model**: Toggle between drag calculation methods
  - **Linear** (True): F = -k * v (simplified, proportional to velocity)
  - **Quadratic** (False): Full drag equation (proportional to v²)

## Behavior

- Always opposes direction of motion
- Linear model: Force decreases linearly with lower speeds
- Quadratic model: Force decreases exponentially with lower speeds (more realistic for higher velocities)
- Automatically deactivates at very low speeds to prevent numerical issues
- Does not depend on mass (buoyancy not modeled)

## Velocity Dependence

- Linear model: Higher speeds produce proportionally higher drag
- Quadratic model: Drag force increases with square of velocity (dominates at high speeds)
