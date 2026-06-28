"""Performance test for numpy-optimized physics engine."""

from __future__ import annotations

import cProfile
import io
import logging
import pstats
import time
from collections.abc import Sequence

import numpy as np

from physics_sim import Ball, DragForce, LinearGravityForce, NumpyPhysicsEngine

logger = logging.getLogger(__name__)

DEFAULT_STEPS = 600
DEFAULT_TEST_CASES: list[int] = [10, 50, 100, 200, 500, 1000]


def benchmark_engine_performance(n_balls: int, n_steps: int = DEFAULT_STEPS) -> float:
    """Test the physics engine with a fixed number of balls and steps."""
    print(f"\n{'=' * 60}")
    print(f"Testing with {n_balls} balls for {n_steps} steps")
    print(f"{'=' * 60}")

    engine = _build_engine(bounds=(20.0, 15.0))

    print(f"Adding {n_balls} balls...")
    start_add = time.time()
    for i in range(n_balls):
        x = (i % 20) + 1.0
        y = ((i // 20) % 10) + 1.0
        ball = Ball(
            position=np.array([x, y]),
            velocity=np.array([np.random.uniform(-5, 5), np.random.uniform(-5, 5)]),
            radius=0.15,
            mass=1.0,
            color=(255, 0, 0),
            restitution=0.9,
        )
        engine.add_entity(ball)
    add_time = time.time() - start_add
    print(
        f"Added {n_balls} balls in {add_time:.3f}s ({n_balls / add_time:.0f} balls/sec)"
    )

    print(f"\nRunning {n_steps} physics steps...")
    dt = 1.0 / 60.0

    start = time.time()
    for _ in range(n_steps):
        engine.step(dt)

    elapsed = time.time() - start

    print("\nResults:")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Steps per second: {n_steps / elapsed:.1f}")
    print(f"  Time per step: {elapsed / n_steps * 1000:.2f}ms")
    print(f"  Equivalent FPS: {n_steps / elapsed:.1f}")

    if n_steps / elapsed >= 60:
        print("  ✓ Target 60 FPS achieved!")
    else:
        print("  ✗ Below 60 FPS target")

    entities = engine.get_inventory_data()
    print(f"\n  Entities in simulation: {len(entities)}")

    return n_steps / elapsed


def run_performance_suite(
    test_cases: Sequence[int] = DEFAULT_TEST_CASES, n_steps: int = DEFAULT_STEPS
) -> dict[int, float]:
    results: dict[int, float] = {}
    for n_balls in test_cases:
        try:
            fps = benchmark_engine_performance(n_balls, n_steps=n_steps)
            results[n_balls] = fps
        except Exception as exc:
            logger.exception("Performance case failed for %d balls", n_balls)
            raise RuntimeError("Aborting performance suite") from exc
    return results


def profile_engine(
    n_balls: int,
    n_steps: int = DEFAULT_STEPS,
    sort_stats: str = "cumtime",
    max_lines: int = 40,
) -> float:
    profiler = cProfile.Profile()
    profiler.enable()
    fps = benchmark_engine_performance(n_balls, n_steps=n_steps)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats(sort_stats)
    stats.print_stats(max_lines)
    logger.info(
        "Profiling summary for %d balls (%d steps):\n%s",
        n_balls,
        n_steps,
        stream.getvalue(),
    )
    return fps


#### END PUBLIC API


def _build_engine(bounds: tuple[float, float]) -> NumpyPhysicsEngine:
    engine = NumpyPhysicsEngine(bounds=bounds)
    engine.add_force(LinearGravityForce(np.array([0.0, -9.81])))
    engine.add_force(DragForce(linear=True))
    return engine


def _print_summary(results: dict[int, float]) -> None:
    print(f"\n{'=' * 60}")
    print("PERFORMANCE SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'Balls':<10} {'FPS':<10} {'Status'}")
    print(f"{'-' * 10} {'-' * 10} {'-' * 30}")
    for n_balls, fps in results.items():
        status = "✓ 60+ FPS" if fps >= 60 else "✗ Below 60 FPS"
        print(f"{n_balls:<10} {fps:<10.1f} {status}")


def main() -> None:
    print("Numpy Physics Engine Performance Test")
    print("=" * 60)
    try:
        results = run_performance_suite()
    except RuntimeError as exc:
        logger.error("Performance suite aborted: %s", exc)
        return

    _print_summary(results)


if __name__ == "__main__":
    main()
