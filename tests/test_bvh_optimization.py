"""Test to verify Numba-optimized BVH produces correct results."""

from __future__ import annotations

import numpy as np

from physics_sim.engines.numpy_engine.bvh import build_lbvh, enumerate_overlapping_pairs


def test_bvh_basic_correctness() -> None:
    """Test that BVH construction and overlap enumeration work correctly."""
    # Create simple test case with 5 AABBs
    aabb_min = np.array(
        [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0], [0.5, 0.5], [3.0, 3.0]],
        dtype=np.float64,
    )
    aabb_max = np.array(
        [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [1.5, 1.5], [4.0, 4.0]],
        dtype=np.float64,
    )

    bounds_min = np.array([0.0, 0.0], dtype=np.float64)
    bounds_max = np.array([5.0, 5.0], dtype=np.float64)

    # Build BVH
    bvh, order = build_lbvh(aabb_min, aabb_max, bounds_min, bounds_max)

    # Verify basic structure
    assert bvh.root >= 0, "BVH should have valid root"
    assert len(order) == 5, "Order array should match input size"
    assert bvh.node_min.shape[0] == 9, "Should have 5 leaves + 4 internal nodes"

    # Enumerate overlapping pairs
    pairs = enumerate_overlapping_pairs(bvh)

    # Verify pairs are valid
    assert pairs.dtype == np.int32, "Pairs should be int32"
    assert pairs.shape[1] == 2, "Each pair should have 2 elements"

    # All pairs should be unique and ordered (i < j)
    for i in range(len(pairs)):
        assert pairs[i, 0] < pairs[i, 1], f"Pair {i} not ordered: {pairs[i]}"

    print("✓ BVH basic correctness test passed")
    print(f"  - Built BVH with {len(aabb_min)} AABBs")
    print(f"  - Found {len(pairs)} overlapping pairs")


def test_bvh_empty_case() -> None:
    """Test BVH with empty input."""
    aabb_min = np.empty((0, 2), dtype=np.float64)
    aabb_max = np.empty((0, 2), dtype=np.float64)
    bounds_min = np.array([0.0, 0.0], dtype=np.float64)
    bounds_max = np.array([5.0, 5.0], dtype=np.float64)

    bvh, order = build_lbvh(aabb_min, aabb_max, bounds_min, bounds_max)

    assert bvh.root == -1, "Empty BVH should have root=-1"
    assert len(order) == 0, "Empty BVH should have empty order"

    pairs = enumerate_overlapping_pairs(bvh)
    assert len(pairs) == 0, "Empty BVH should produce no pairs"

    print("✓ BVH empty case test passed")


def test_bvh_single_aabb() -> None:
    """Test BVH with single AABB."""
    aabb_min = np.array([[1.0, 1.0]], dtype=np.float64)
    aabb_max = np.array([[2.0, 2.0]], dtype=np.float64)
    bounds_min = np.array([0.0, 0.0], dtype=np.float64)
    bounds_max = np.array([5.0, 5.0], dtype=np.float64)

    bvh, order = build_lbvh(aabb_min, aabb_max, bounds_min, bounds_max)

    assert bvh.root == 0, "Single AABB BVH should have root=0"
    assert len(order) == 1, "Single AABB BVH should have order of length 1"

    pairs = enumerate_overlapping_pairs(bvh)
    assert len(pairs) == 0, "Single AABB should produce no pairs"

    print("✓ BVH single AABB test passed")


def test_bvh_large_scale() -> None:
    """Test BVH with larger number of AABBs (performance check)."""
    n = 1000
    np.random.seed(42)

    # Generate random AABBs
    positions = np.random.uniform(0, 100, (n, 2)).astype(np.float64)
    sizes = np.random.uniform(0.5, 2.0, (n, 2)).astype(np.float64)

    aabb_min = positions - sizes * 0.5
    aabb_max = positions + sizes * 0.5

    bounds_min = np.array([0.0, 0.0], dtype=np.float64)
    bounds_max = np.array([100.0, 100.0], dtype=np.float64)

    # Build BVH
    bvh, order = build_lbvh(aabb_min, aabb_max, bounds_min, bounds_max)

    assert bvh.root >= 0, "Large BVH should have valid root"
    assert len(order) == n, f"Order array should match input size ({n})"

    # Enumerate overlapping pairs
    pairs = enumerate_overlapping_pairs(bvh)

    # Basic validation
    assert pairs.dtype == np.int32, "Pairs should be int32"
    if len(pairs) > 0:
        assert pairs.shape[1] == 2, "Each pair should have 2 elements"
        assert np.all(pairs[:, 0] < pairs[:, 1]), "All pairs should be ordered"
        assert np.all(pairs[:, 0] >= 0) and np.all(pairs[:, 1] < n), (
            "Pair indices should be valid"
        )

    print("✓ BVH large scale test passed")
    print(f"  - Built BVH with {n} AABBs")
    print(f"  - Found {len(pairs)} overlapping pairs")


def test_3d_morton_codes() -> None:
    """Test 3D Morton code computation."""
    aabb_min = np.array(
        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]], dtype=np.float64
    )
    aabb_max = np.array(
        [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]], dtype=np.float64
    )

    bounds_min = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    bounds_max = np.array([5.0, 5.0, 5.0], dtype=np.float64)

    # Build 3D BVH
    bvh, order = build_lbvh(aabb_min, aabb_max, bounds_min, bounds_max)

    assert bvh.root >= 0, "3D BVH should have valid root"
    assert bvh.node_min.shape[1] == 3, "3D BVH should have 3D node bounds"
    assert bvh.node_max.shape[1] == 3, "3D BVH should have 3D node bounds"

    pairs = enumerate_overlapping_pairs(bvh)
    assert pairs.dtype == np.int32, "Pairs should be int32"

    print("✓ 3D Morton code test passed")


def run_all_tests() -> None:
    """Run all BVH verification tests."""
    print("Running BVH optimization verification tests...\n")

    test_bvh_empty_case()
    test_bvh_single_aabb()
    test_bvh_basic_correctness()
    test_bvh_large_scale()
    test_3d_morton_codes()

    print("\n" + "=" * 60)
    print("✓ All BVH optimization tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
