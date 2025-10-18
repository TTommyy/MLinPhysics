"""Performance test for numpy-optimized physics engine."""

import time

import numpy as np

from physics_sim import Ball, DragForce, LinearGravityForce, NumpyPhysicsEngine


def test_engine_performance(n_balls: int, n_steps: int = 600):
    """Test physics engine with specified number of balls."""
    print(f"\n{'=' * 60}")
    print(f"Testing with {n_balls} balls for {n_steps} steps")
    print(f"{'=' * 60}")

    # Create engine
    engine = NumpyPhysicsEngine(
        bounds=(20.0, 15.0),
    )

    # Add forces
    engine.add_force(LinearGravityForce(np.array([0.0, -9.81])))
    engine.add_force(DragForce(linear=True))

    # Add many balls
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

    # Run simulation
    print(f"\nRunning {n_steps} physics steps...")
    dt = 1.0 / 60.0

    start = time.time()
    for step in range(n_steps):
        engine.step(dt)

    elapsed = time.time() - start

    # Results
    print("\nResults:")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Steps per second: {n_steps / elapsed:.1f}")
    print(f"  Time per step: {elapsed / n_steps * 1000:.2f}ms")
    print(f"  Equivalent FPS: {n_steps / elapsed:.1f}")

    if n_steps / elapsed >= 60:
        print("  ✓ Target 60 FPS achieved!")
    else:
        print("  ✗ Below 60 FPS target")

    # Check entities still exist
    entities = engine.get_entities()
    print(f"\n  Entities in simulation: {len(entities)}")

    return n_steps / elapsed


def main():
    """Run performance tests with increasing ball counts."""
    print("Numpy Physics Engine Performance Test")
    print("=" * 60)

    test_cases = [10, 50, 100, 200, 500, 1000]
    results = {}

    for n_balls in test_cases:
        try:
            fps = test_engine_performance(n_balls, n_steps=600)
            results[n_balls] = fps
        except Exception as e:
            print(f"\nError with {n_balls} balls: {e}")
            import traceback

            traceback.print_exc()
            break

    # Summary
    print(f"\n{'=' * 60}")
    print("PERFORMANCE SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'Balls':<10} {'FPS':<10} {'Status'}")
    print(f"{'-' * 10} {'-' * 10} {'-' * 30}")
    for n_balls, fps in results.items():
        status = "✓ 60+ FPS" if fps >= 60 else "✗ Below 60 FPS"
        print(f"{n_balls:<10} {fps:<10.1f} {status}")


if __name__ == "__main__":
    main()
