"""simulation smoke test; step the engine for 2s with a few balls."""

import numpy as np
import pytest

from physics_sim import Ball, DragForce, LinearGravityForce, NumpyPhysicsEngine

DT = 1.0 / 60.0
DURATION = 2.0
STEPS = int(DURATION / DT)

BOUNDS = (20.0, 15.0)
N_BALLS = 5

_BALL_SPECS = (
    ((3.0, 7.0), (5.0, 0.0)),
    ((6.0, 10.0), (-3.0, 2.0)),
    ((9.0, 5.0), (2.0, -4.0)),
    ((12.0, 11.0), (-4.0, -1.0)),
    ((15.0, 7.0), (3.0, 3.0)),
)


def _build_engine() -> NumpyPhysicsEngine:
    engine = NumpyPhysicsEngine(bounds=BOUNDS)
    engine.add_force(LinearGravityForce(acceleration=np.array([0.0, -9.81])))
    engine.add_force(DragForce())
    for pos, vel in _BALL_SPECS:
        engine.add_entity(
            Ball(
                position=np.array(pos, dtype=np.float64),
                velocity=np.array(vel, dtype=np.float64),
                radius=0.5,
                mass=1.0,
                color=(255, 0, 0),
                restitution=0.9,
            )
        )
    return engine


def test_simulation_runs_for_two_seconds_without_error() -> None:
    try:
        engine = _build_engine()
        for _ in range(STEPS):
            engine.step(DT)
    except Exception as exc:
        pytest.fail(f"simulation raised {type(exc).__name__} within {DURATION}s: {exc}")

    n = engine._n_entities
    assert n == N_BALLS, f"entity count changed during run: {N_BALLS} -> {n}"
    positions = engine._positions[:n]
    assert np.all(np.isfinite(positions)), (
        f"non-finite positions after {DURATION}s:\n{positions}"
    )
