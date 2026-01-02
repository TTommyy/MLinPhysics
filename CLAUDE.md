# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modular 2D physics simulation framework with a pluggable engine architecture. Uses Arcade for rendering and NumPy/Numba for physics computations.

## Commands

### Run the simulation
```bash
uv run python main.py
```

### Development mode (hot-reload)
```bash
uv run python dev.py
```

### Run tests
```bash
uv run pytest                    # all tests
uv run pytest tests/test_performance.py  # single test file
uv run pytest -k "test_name"     # specific test
```

### Linting and formatting
```bash
uv run ruff check .
uv run black .
```

## Architecture

### Core Abstractions (`physics_sim/core/`)
- **PhysicsEngine**: Abstract base class for physics implementations (Strategy pattern)
- **Entity/PhysicalEntity**: Base classes for simulation objects with position, velocity, mass
- **Force**: Abstract base for force implementations with vectorized `apply_force()` for batch processing
- **Renderer**: Abstract base for rendering backends

### NumpyPhysicsEngine (`physics_sim/engines/numpy_engine/`)
The main physics engine uses Structure-of-Arrays (SoA) for efficient vectorized computation:
- **StorageMixin**: Manages NumPy arrays for positions, velocities, masses, entity types
- **CollisionMixin**: Ball-ball and ball-obstacle collision detection/resolution
- **BroadphaseMixin**: BVH-based spatial partitioning for collision broad phase
- **IntegrationMixin**: Euler integration
- **PBDMixin**: Position-Based Dynamics constraint solver
- **ForceMixin**: Applies registered Force instances each step

Collision detection can use BVH (`bvh=True`) or naive vectorized approach.

### Forces (`physics_sim/forces/`)
Forces implement vectorized `apply_force()` receiving batch arrays:
- LinearGravityForce, CentralGravityForce
- DragForce (air resistance)
- VortexForce
- PBD constraints: WireConstraintPBDForce, SpringTetherPBDFore, PairwiseDistancePBDFore

### Simulation (`physics_sim/simulation/`)
- **SimulationConfig**: Dataclass with screen/physics/layout parameters
- **Simulator**: Arcade Window subclass orchestrating engine, sections, and input

### UI (`physics_sim/ui/`)
Section-based Arcade UI with ControlPanel, InventoryPanel, Viewport, ForceManager, EnergyManager sections.

## Key Patterns

1. **Dependency Injection**: `Simulator` receives `PhysicsEngine` instance, allowing engine swapping
2. **Mixin Composition**: `NumpyPhysicsEngine` composed from specialized mixins
3. **Vectorized Force API**: Forces receive NumPy arrays (positions, velocities, masses) and return force vectors for all entities at once
4. **Entity Type System**: Entities identified by type IDs; type-specific properties stored in dictionaries indexed by type