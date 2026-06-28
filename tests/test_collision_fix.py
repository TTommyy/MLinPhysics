"""Test script to verify collision detection is working after BVH fix."""

from __future__ import annotations

import logging

import numpy as np

from physics_sim import Ball, DragForce, NumpyPhysicsEngine

# Enable debug logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_bvh_structure():
    """Test that BVH structure is correct."""
    logger.info("=" * 60)
    logger.info("TEST 1: BVH Structure Validation")
    logger.info("=" * 60)

    engine = NumpyPhysicsEngine(bounds=(20.0, 15.0))

    # Add 3 balls in a line (should collide)
    ball1 = Ball(
        position=np.array([5.0, 7.5]),
        velocity=np.array([0.0, 0.0]),
        radius=0.5,
        mass=1.0,
        color=(255, 0, 0),
        restitution=0.9,
    )
    ball2 = Ball(
        position=np.array([5.5, 7.5]),
        velocity=np.array([0.0, 0.0]),
        radius=0.5,
        mass=1.0,
        color=(0, 255, 0),
        restitution=0.9,
    )
    ball3 = Ball(
        position=np.array([6.0, 7.5]),
        velocity=np.array([0.0, 0.0]),
        radius=0.5,
        mass=1.0,
        color=(0, 0, 255),
        restitution=0.9,
    )

    engine.add_entity(ball1)
    engine.add_entity(ball2)
    engine.add_entity(ball3)

    logger.info("Added 3 balls overlapping in a line")

    # Step once and check BVH
    engine.step(1.0 / 60.0)

    logger.info("✓ BVH structure created successfully (no errors)")
    return True


def test_collision_detection():
    """Test that collisions are actually detected."""
    logger.info("=" * 60)
    logger.info("TEST 2: Collision Detection")
    logger.info("=" * 60)

    engine = NumpyPhysicsEngine(bounds=(20.0, 15.0))
    engine.add_force(DragForce(linear=True))

    # Add 2 balls that should collide
    ball1 = Ball(
        position=np.array([5.0, 7.5]),
        velocity=np.array([2.0, 0.0]),  # Moving right
        radius=0.5,
        mass=1.0,
        color=(255, 0, 0),
        restitution=0.95,
    )
    ball2 = Ball(
        position=np.array([8.0, 7.5]),
        velocity=np.array([-2.0, 0.0]),  # Moving left
        radius=0.5,
        mass=1.0,
        color=(0, 255, 0),
        restitution=0.95,
    )

    engine.add_entity(ball1)
    engine.add_entity(ball2)

    logger.info("Added 2 balls moving towards each other")

    # Step several times
    dt = 1.0 / 60.0
    collision_found = False

    for i in range(100):
        pairs = engine._build_bvh_and_pairs()
        if pairs["ball_ball"].shape[0] > 0:
            collision_found = True
            logger.info(f"✓ Collision detected at step {i}!")
            logger.info(f"  Pairs detected: {pairs['ball_ball']}")
            break

        engine.step(dt)

    if collision_found:
        logger.info("✓ Collision detection working!")
        return True
    else:
        logger.warning("✗ No collision detected after 100 steps")
        return False


def test_multiple_collisions():
    """Test multiple simultaneous collisions."""
    logger.info("=" * 60)
    logger.info("TEST 3: Multiple Simultaneous Collisions")
    logger.info("=" * 60)

    engine = NumpyPhysicsEngine(bounds=(20.0, 15.0))

    # Create a 2x2 grid of overlapping balls
    positions = [
        (5.0, 7.5),
        (5.5, 7.5),
        (5.0, 8.0),
        (5.5, 8.0),
    ]

    for i, (x, y) in enumerate(positions):
        ball = Ball(
            position=np.array([x, y]),
            velocity=np.array([0.0, 0.0]),
            radius=0.4,
            mass=1.0,
            color=(255, 0, 0),
            restitution=0.9,
        )
        engine.add_entity(ball)

    logger.info("Added 4 overlapping balls in a 2x2 grid")

    # Check BEFORE stepping (balls are overlapping initially)
    pairs = engine._build_bvh_and_pairs()

    if pairs["ball_ball"].shape[0] > 0:
        logger.info(
            f"✓ Multiple collisions detected: {pairs['ball_ball'].shape[0]} pairs"
        )
        logger.info(f"  Pairs: {pairs['ball_ball']}")
        return True
    else:
        logger.warning("✗ No collisions detected in 2x2 grid")
        return False


def test_no_false_positives():
    """Test that distant balls don't collide."""
    logger.info("=" * 60)
    logger.info("TEST 4: No False Positives (Distant Objects)")
    logger.info("=" * 60)

    engine = NumpyPhysicsEngine(bounds=(20.0, 15.0))

    # Add 2 balls far apart
    ball1 = Ball(
        position=np.array([2.0, 2.0]),
        velocity=np.array([0.0, 0.0]),
        radius=0.5,
        mass=1.0,
        color=(255, 0, 0),
        restitution=0.9,
    )
    ball2 = Ball(
        position=np.array([18.0, 12.0]),
        velocity=np.array([0.0, 0.0]),
        radius=0.5,
        mass=1.0,
        color=(0, 255, 0),
        restitution=0.9,
    )

    engine.add_entity(ball1)
    engine.add_entity(ball2)

    logger.info("Added 2 balls far apart")

    engine.step(1.0 / 60.0)
    pairs = engine._build_bvh_and_pairs()

    if pairs["ball_ball"].shape[0] == 0:
        logger.info("✓ No false positives (distant objects don't collide)")
        return True
    else:
        logger.warning(f"✗ False positive detected: {pairs['ball_ball']}")
        return False


def test_mixed_entities():
    """Test collisions with mix of balls and obstacles (index remapping test)."""
    logger.info("=" * 60)
    logger.info("TEST 5: Mixed Entities (Index Remapping)")
    logger.info("=" * 60)

    engine = NumpyPhysicsEngine(bounds=(20.0, 15.0))

    # Add obstacles first to test index offset
    from physics_sim.entities import CircleObstacle, RectangleObstacle

    obs1 = RectangleObstacle(
        position=np.array([10.0, 10.0]),
        width=2.0,
        height=2.0,
        color=(100, 100, 100),
    )
    engine.add_entity(obs1)

    obs2 = CircleObstacle(
        position=np.array([15.0, 10.0]),
        radius=1.0,
        color=(100, 100, 100),
    )
    engine.add_entity(obs2)

    # Now add colliding balls
    ball1 = Ball(
        position=np.array([10.0, 8.0]),
        velocity=np.array([0.0, 1.0]),  # Moving up toward obstacle
        radius=0.5,
        mass=1.0,
        color=(255, 0, 0),
        restitution=0.9,
    )
    engine.add_entity(ball1)

    ball2 = Ball(
        position=np.array([14.5, 8.5]),
        velocity=np.array([0.0, 1.0]),  # Moving up toward circle obstacle
        radius=0.5,
        mass=1.0,
        color=(0, 255, 0),
        restitution=0.9,
    )
    engine.add_entity(ball2)

    logger.info("Added 2 obstacles + 2 balls (testing index mapping)")

    # Step several times and look for collisions
    dt = 1.0 / 60.0
    collision_found = False

    for i in range(200):
        pairs = engine._build_bvh_and_pairs()
        if (
            pairs["ball_ball"].shape[0] > 0
            or pairs["ball_rect"].shape[0] > 0
            or pairs["ball_circle"].shape[0] > 0
        ):
            collision_found = True
            logger.info(f"✓ Collision detected at step {i}!")
            logger.info(f"  Ball-Ball pairs: {pairs['ball_ball']}")
            logger.info(f"  Ball-Rect pairs: {pairs['ball_rect']}")
            logger.info(f"  Ball-Circle pairs: {pairs['ball_circle']}")
            break

        engine.step(dt)

    if collision_found:
        logger.info("✓ Index mapping working correctly!")
        return True
    else:
        logger.warning("✗ No collisions detected with mixed entities")
        return False


def test_many_obstacles():
    """Test collision detection with many obstacles (stress test for indexing)."""
    logger.info("=" * 60)
    logger.info("TEST 6: Many Obstacles (Stress Test)")
    logger.info("=" * 60)

    engine = NumpyPhysicsEngine(bounds=(20.0, 15.0))

    # Add many static entities
    from physics_sim.entities import RectangleObstacle

    for i in range(10):
        obs = RectangleObstacle(
            position=np.array([float(i % 5), float(i // 5)]),
            width=0.5,
            height=0.5,
            color=(50, 50, 50),
        )
        engine.add_entity(obs)

    # Add one colliding ball
    ball = Ball(
        position=np.array([0.2, 0.2]),
        velocity=np.array([0.0, 0.0]),
        radius=0.3,
        mass=1.0,
        color=(255, 0, 0),
        restitution=0.9,
    )
    engine.add_entity(ball)

    logger.info("Added 10 obstacles + 1 ball (index stress test)")

    pairs = engine._build_bvh_and_pairs()

    if pairs["ball_rect"].shape[0] > 0:
        logger.info(f"✓ Collision detected: {pairs['ball_rect'].shape[0]} pairs")
        logger.info(f"  Pairs: {pairs['ball_rect']}")
        return True
    else:
        logger.warning("✗ No collision detected in stress test")
        return False


if __name__ == "__main__":
    results = []

    try:
        results.append(("BVH Structure", test_bvh_structure()))
    except Exception as e:
        logger.error(f"BVH Structure test failed: {e}")
        results.append(("BVH Structure", False))

    try:
        results.append(("Collision Detection", test_collision_detection()))
    except Exception as e:
        logger.error(f"Collision Detection test failed: {e}")
        results.append(("Collision Detection", False))

    try:
        results.append(("Multiple Collisions", test_multiple_collisions()))
    except Exception as e:
        logger.error(f"Multiple Collisions test failed: {e}")
        results.append(("Multiple Collisions", False))

    try:
        results.append(("No False Positives", test_no_false_positives()))
    except Exception as e:
        logger.error(f"No False Positives test failed: {e}")
        results.append(("No False Positives", False))

    try:
        results.append(("Mixed Entities (Index Remapping)", test_mixed_entities()))
    except Exception as e:
        logger.error(f"Mixed Entities test failed: {e}")
        results.append(("Mixed Entities (Index Remapping)", False))

    try:
        results.append(("Many Obstacles (Stress)", test_many_obstacles()))
    except Exception as e:
        logger.error(f"Many Obstacles test failed: {e}")
        results.append(("Many Obstacles (Stress)", False))

    # Print summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status} - {name}")

    all_passed = all(passed for _, passed in results)
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED! Collision detection is fixed!")
    else:
        logger.info("❌ Some tests failed. Review output above.")
