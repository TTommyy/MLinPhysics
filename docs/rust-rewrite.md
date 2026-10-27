# Rust Rewrite Plan

> **Status:** Original architecture and technology recommendation. The authoritative
> execution roadmap is [`../rust/PLAN.md`](../rust/PLAN.md), and the complete Python
> parity inventory is [`../rust/PYTHON_FEATURES.md`](../rust/PYTHON_FEATURES.md).
> Keep this document as background research; do not use its milestones or dependency
> versions as the active implementation sequence.

## Goal

Rewrite the project as a learning-focused, high-performance 2D physics simulator in Rust.

The rewrite should teach all three areas:

- systems and performance: memory layout, cache behavior, parallelism, profiling
- graphics and UI: real-time rendering, debug visualization, interactive controls
- physics and numerical methods: integration, constraints, collision detection, BVH broadphase

The project should stay 2D. Avoid adding 3D until the 2D engine is fast, well-tested, and easy to inspect.

## Recommendation

Use a custom data-oriented physics engine in Rust.

Start with `macroquad` for rendering because it keeps the feedback loop short. Add `wgpu` later when the CPU-side simulation is stable and the project is ready for GPU instancing or compute experiments.

Do not start with a full engine such as Bevy. Bevy is useful, but it teaches Bevy's ECS and engine architecture before the physics architecture is understood. For this project, building the core storage and simulation loop directly is more valuable.

## Core Stack

### `glam`

Use for vector math.

Why:

- fast, game-oriented math types
- simple `Vec2` API
- good fit for 2D physics and rendering
- avoids writing low-level vector types too early

Links:

- <https://crates.io/crates/glam>
- <https://docs.rs/glam>

### `macroquad`

Use for the first renderer and application loop.

Why:

- very fast to get a real-time 2D app on screen
- good enough for circles, obstacles, vector fields, trails, debug overlays
- simple desktop and web targets
- less framework weight than a full game engine

Links:

- <https://crates.io/crates/macroquad>
- <https://docs.rs/macroquad>

### `egui`

Use for interactive controls.

Why:

- immediate-mode UI is a good fit for simulation tools
- force sliders, toggles, debug panels, entity inspectors, and benchmark controls are straightforward
- pairs well with a custom engine because UI can emit simple commands

Links:

- <https://crates.io/crates/egui>
- <https://docs.rs/egui>

### `rayon`

Use for CPU parallelism once the serial implementation is correct.

Good targets:

- force accumulation
- integration
- AABB generation
- BVH pair filtering
- collision candidate processing

Links:

- <https://crates.io/crates/rayon>
- <https://docs.rs/rayon>

### `criterion`

Use for serious benchmarks.

Why:

- stable benchmark harness
- useful statistics
- good for comparing broadphase versions, integrators, collision resolution, and storage layouts

Links:

- <https://crates.io/crates/criterion>
- <https://docs.rs/criterion>

### `wgpu`

Use later for the high-performance renderer and GPU learning.

Use WGSL as the canonical shader source for native and browser builds. Learn it in
small laboratories before the final renderer: first vertex/fragment basics and
uniforms, then instanced circles and debug vectors, then production pipelines.
WebAssembly drives `wgpu`/WebGPU from the CPU side; WGSL executes on the GPU.

Good targets:

- instanced rendering for many balls
- GPU-side trails or heatmaps
- vector field rendering
- optional compute shader experiments

Do not use `wgpu` on day one unless the learning goal is graphics first. It will slow down the first physics milestones.

Links:

- <https://crates.io/crates/wgpu>
- <https://docs.rs/wgpu>

## Supporting Crates

### Serialization

Use `serde` plus one readable scene format.

Recommended:

- `serde`
- `ron` or `toml`

Use for:

- saved scenes
- force presets
- benchmark scenarios
- regression fixtures

### Logging and Profiling Hooks

Use:

- `tracing`
- `tracing-subscriber`

Use for:

- frame timing
- broadphase timing
- pair counts
- collision counts
- force evaluation timing

### GPU Buffer Utilities

Use `bytemuck` when adding `wgpu`.

Use for:

- safe plain-old-data casts
- instance buffers
- uniform buffers

### Entity Handles

Use one of:

- `slotmap`
- `generational-arena`

Use only if raw indices become unsafe or hard to manage. For the first version, dense integer IDs may be enough.

### Small Allocations

Use `smallvec` only where profiling shows many tiny heap allocations.

Likely places:

- temporary contact lists
- small debug draw batches
- small command buffers

### Fast Hash Maps

Use one of:

- `rustc-hash`
- `ahash`

Use only for non-adversarial internal maps. Do not put hash maps in hot loops unless profiling proves it is fine.

### Property Testing

Use `proptest`.

Useful invariants:

- collision pairs are unique
- no self-pairs
- collision normal is finite
- energy does not become NaN
- BVH pair output is a superset of brute-force overlap output

### Snapshot Testing

Use `insta` for serialized state snapshots.

Good targets:

- saved scene format
- force configuration
- debug statistics output

## Reference Physics Engine

Use `rapier2d` as a reference, not as the main engine.

Why:

- compare behavior
- compare performance
- learn how a mature physics library structures colliders, handles, and broadphase

Do not build the rewrite on top of Rapier if the goal is learning physics internals.

Link:

- <https://github.com/dimforge/rapier>

## Architecture

Use a data-oriented ECS-lite design.

Avoid object-oriented entity hierarchies. Keep data in dense arrays and run systems over those arrays.

### Suggested Crates in the Workspace

```text
physics-rs/
  crates/
    physics_core/      # storage, forces, integration, collisions, BVH
    physics_app/       # macroquad app, input, UI, rendering
    physics_bench/     # criterion benchmarks
```

### Core Data Layout

Use struct-of-arrays storage:

```text
positions: Vec<Vec2>
velocities: Vec<Vec2>
forces: Vec<Vec2>
radii: Vec<f32>
masses: Vec<f32>
restitution: Vec<f32>
entity_kind: Vec<EntityKind>
active: Vec<bool>
```

This layout makes it easier to:

- iterate cache-efficiently
- parallelize loops
- build AABBs in batches
- benchmark isolated systems

### Simulation Loop

Use a fixed timestep:

```text
accumulate time
while accumulator >= dt:
  clear force accumulators
  apply forces
  integrate velocities
  build AABBs
  build BVH
  enumerate candidate pairs
  resolve collisions and constraints
  integrate positions
  accumulator -= dt
render interpolated state
```

Keep the renderer read-only with respect to simulation state. UI should send commands, not mutate random fields directly.

### Command Boundary

Use simple commands from UI to engine:

```text
AddBall
RemoveEntity
SetForceEnabled
SetForceParameter
Pause
StepOnce
ResetScene
LoadScene
SaveScene
```

This keeps the engine testable without a window.

## Performance Strategy

### First Rule

Get the scalar, single-threaded version correct first.

Only optimize after there are:

- correctness tests
- benchmark scenes
- profiling output
- a simple way to compare against brute force

### Hot Paths

Expected hot paths:

- force accumulation
- AABB generation
- BVH construction
- pair enumeration
- collision resolution
- rendering many entities

### Optimization Order

1. Dense storage and simple loops
2. Remove avoidable allocations from the frame loop
3. Benchmark brute force vs BVH
4. Parallelize independent loops with `rayon`
5. Add rendering instancing
6. Consider GPU compute only after CPU limits are clear

## Milestones

### Milestone 1: Minimal 2D Engine

Features:

- balls
- gravity
- drag
- wall collisions
- fixed timestep
- macroquad rendering

Verification:

- unit tests for integration
- no NaNs after long run
- simple benchmark for 100, 1,000, and 10,000 balls

### Milestone 2: Obstacles and Forces

Features:

- circle obstacles
- rectangle obstacles
- vortex force
- central gravity
- spring/tether style constraints

Verification:

- deterministic scene fixtures
- collision invariants
- force parameter tests

### Milestone 3: BVH Broadphase

Features:

- 2D Morton codes
- LBVH build
- pair enumeration
- brute-force comparison mode

Verification:

- BVH pairs are a superset of brute-force overlaps
- no duplicate pairs
- benchmark broadphase scaling

### Milestone 4: UI and Debugging

Features:

- force toggles
- force parameter editor
- entity inspector
- collision pair count
- broadphase timing
- frame timing
- pause and step controls

Verification:

- engine remains usable headless
- UI commands are tested separately from simulation systems

### Milestone 5: Performance Pass

Features:

- no frame-loop heap allocation in core systems where practical
- `rayon` parallel loops
- benchmark dashboard
- optional flamegraph/profiling workflow

Verification:

- benchmark reports committed for standard scenes
- performance does not regress without an explicit reason

### Milestone 6: `wgpu` Renderer

Features:

- instanced ball rendering
- obstacle rendering
- vector field overlay
- optional trails

Verification:

- macroquad renderer still available as simple backend, or deliberately removed after `wgpu` is stable
- render benchmarks for large entity counts

## What Not To Do First

Avoid these at the beginning:

- full ECS framework
- networking
- save-file version migration
- GPU compute
- 3D
- complex constraint solver
- perfect editor UI

These can come later. The first target is a fast, testable 2D physics core.

## Initial Dependency Set

Start with:

```toml
[dependencies]
glam = "0.30"
macroquad = "0.4"
egui = "0.32"
serde = { version = "1", features = ["derive"] }
ron = "0.10"
tracing = "0.1"
tracing-subscriber = "0.3"

[dev-dependencies]
criterion = "0.7"
proptest = "1"
insta = "1"
```

Add later:

```toml
rayon = "1"
wgpu = "26"
bytemuck = { version = "1", features = ["derive"] }
slotmap = "1"
smallvec = "1"
rustc-hash = "2"
```

Version numbers should be refreshed when the Rust workspace is created.

## Recommended First Step

Create a new Rust workspace next to the Python implementation rather than deleting the Python code.

Suggested path:

```text
rust/
  Cargo.toml
  crates/
    physics_core/
    physics_app/
    physics_bench/
```

Keep the Python project as a reference implementation until the Rust version passes equivalent behavior and benchmark tests.
