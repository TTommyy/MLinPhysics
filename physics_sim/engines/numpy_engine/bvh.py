from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from numba import njit

# Configure logging
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LBVH:
    left: np.ndarray
    right: np.ndarray
    parent: np.ndarray
    node_min: np.ndarray
    node_max: np.ndarray
    leaf_index: np.ndarray
    root: int


@njit(cache=True)
def _clz32(x: int) -> int:
    """Count leading zeros in a 32-bit integer (Numba-compatible)."""
    if x <= 0:
        return 32

    # Manual bit counting for Numba compatibility
    n = 0
    if x <= 0x0000FFFF:
        n += 16
        x <<= 16
    if x <= 0x00FFFFFF:
        n += 8
        x <<= 8
    if x <= 0x0FFFFFFF:
        n += 4
        x <<= 4
    if x <= 0x3FFFFFFF:
        n += 2
        x <<= 2
    if x <= 0x7FFFFFFF:
        n += 1

    return n


@njit(cache=True)
def _lcp(i: int, j: int, morton: np.ndarray, n: int) -> int:
    if j < 0 or j >= n:
        return -1
    a = int(morton[i])
    b = int(morton[j])
    if a == b:
        # Tie-breaker by index per Karras 2012
        result = 32 + _clz32(i ^ j)
        return result
    result = _clz32(a ^ b)
    return result


@njit(cache=True, fastmath=True)
def _expand_bits_2d(v: np.ndarray) -> np.ndarray:
    # Interleave 16-bit to 32-bit (up to 10 bits used)
    x = v.astype(np.uint32)
    x = (x | (x << 8)) & np.uint32(0x00FF00FF)
    x = (x | (x << 4)) & np.uint32(0x0F0F0F0F)
    x = (x | (x << 2)) & np.uint32(0x33333333)
    x = (x | (x << 1)) & np.uint32(0x55555555)
    return x


@njit(cache=True, fastmath=True)
def _morton2d(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    xx = _expand_bits_2d(x)
    yy = _expand_bits_2d(y) << np.uint32(1)
    result = xx | yy
    return result


@njit(cache=True, fastmath=True)
def _quantize01(vals: np.ndarray) -> np.ndarray:
    # Map [0,1] -> [0, 1023]
    clipped = np.clip(vals, 0.0, 1.0)
    scaled = clipped * 1023.0
    floored = np.floor(scaled)
    result = floored.astype(np.int32)
    return result


@njit(cache=True, fastmath=True)
def _compute_morton_codes_kernel(
    centers: np.ndarray, bounds_min: np.ndarray, bounds_max: np.ndarray
) -> np.ndarray:
    # Normalize to [0,1]
    size = np.maximum(bounds_max - bounds_min, 1e-12)
    norm = (centers - bounds_min) / size

    qx = _quantize01(norm[:, 0])
    qy = _quantize01(norm[:, 1])
    result = _morton2d(qx, qy).astype(np.uint32)

    return result


def _compute_morton_codes(
    centers: np.ndarray, bounds_min: np.ndarray, bounds_max: np.ndarray
) -> np.ndarray:
    if centers.ndim != 2 or centers.shape[1] != 2:
        raise ValueError("BVH Morton encoding supports 2D centers only")

    logger.info(f"_compute_morton_codes called with centers shape={centers.shape}")
    result = _compute_morton_codes_kernel(centers, bounds_min, bounds_max)
    logger.info(f"_compute_morton_codes returning morton codes shape={result.shape}")
    return result


@njit(cache=True)
def _find_split(first: int, last: int, morton: np.ndarray) -> int:
    # Karras 2012: find index where highest differing bit between first and last splits the range
    first_code = int(morton[first])
    last_code = int(morton[last])

    if first_code == last_code:
        result = (first + last) >> 1
        return result

    common_prefix = _clz32(first_code ^ last_code)

    split = first
    step = last - first

    while step > 1:
        step = (step + 1) >> 1
        new_split = split + step
        if new_split < last:
            split_code = int(morton[new_split])
            prefix = _clz32(first_code ^ split_code)
            if prefix > common_prefix:
                split = new_split
    result = split
    return result


def build_lbvh(
    aabb_min: np.ndarray,
    aabb_max: np.ndarray,
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
) -> tuple[LBVH, np.ndarray]:
    """
    Build a Linear BVH from leaf AABBs using recursive top-down construction.

    Returns (LBVH, leaf_order), where leaf_order maps leaf id -> original collider index.
    """
    logger.info(f"build_lbvh called with aabb_min shape={aabb_min.shape}")
    n = int(aabb_min.shape[0])

    if n == 0:
        logger.info("Empty BVH requested")
        empty = np.empty((0,), dtype=np.int32)
        zeros_2 = np.empty(
            (0, aabb_min.shape[1] if aabb_min.ndim == 2 else 2), dtype=np.float64
        )
        bvh = LBVH(
            left=empty,
            right=empty,
            parent=empty,
            node_min=zeros_2,
            node_max=zeros_2,
            leaf_index=empty,
            root=-1,
        )
        return bvh, empty

    d = aabb_min.shape[1]
    if d != 2:
        raise ValueError("LBVH supports 2D AABBs only")

    centers = 0.5 * (aabb_min + aabb_max)

    morton = _compute_morton_codes(centers, bounds_min[:d], bounds_max[:d])

    order = np.argsort(morton, kind="mergesort")  # stable sort

    aabb_min_sorted = aabb_min[order]
    aabb_max_sorted = aabb_max[order]
    logger.debug(
        f"Sorted AABBs shapes: min={aabb_min_sorted.shape}, max={aabb_max_sorted.shape}"
    )

    # Node indexing: leaves [0..N-1], internals [N..2N-2]
    m = 2 * n - 1

    left = np.full((m,), -1, dtype=np.int32)
    right = np.full((m,), -1, dtype=np.int32)
    parent = np.full((m,), -1, dtype=np.int32)
    node_min = np.zeros((m, d), dtype=np.float64)
    node_max = np.zeros((m, d), dtype=np.float64)
    leaf_index = np.full((m,), -1, dtype=np.int32)

    # Initialize leaves
    node_min[0:n] = aabb_min_sorted
    node_max[0:n] = aabb_max_sorted
    leaf_index[0:n] = order.astype(np.int32)

    if n == 1:
        root = 0
        bvh = LBVH(left, right, parent, node_min, node_max, leaf_index, root)
        logger.info("Single leaf BVH built successfully")
        return bvh, order.astype(np.int32)

    # Precompute LCP accessor in local scope
    def lcp(i: int, j: int) -> int:
        return _lcp(i, j, morton, n)

    # Counter for allocating internal node indices
    next_internal_idx: list[int] = [0]  # Use list to allow mutation in nested function

    def build_subtree_recursive(first: int, last: int) -> int:
        """
        Recursively build a subtree for range [first, last].
        Returns the node index.
        """

        if first == last:
            # Single leaf
            return first

        # Find split point
        split = _find_split(first, last, morton)

        # Recursively build left and right subtrees
        left_node = build_subtree_recursive(first, split)
        right_node = build_subtree_recursive(split + 1, last)

        # Allocate internal node
        this_node = n + next_internal_idx[0]
        next_internal_idx[0] += 1

        # Link children
        left[this_node] = left_node
        right[this_node] = right_node
        parent[left_node] = this_node
        parent[right_node] = this_node

        # Compute AABB by merging children
        node_min[this_node] = np.minimum(node_min[left_node], node_min[right_node])
        node_max[this_node] = np.maximum(node_max[left_node], node_max[right_node])

        return this_node

    # Build tree recursively from root
    logger.info(f"Building tree recursively for {n - 1} internal nodes")
    root = build_subtree_recursive(0, n - 1)
    logger.info(f"Root found at node {root}")

    bvh = LBVH(left, right, parent, node_min, node_max, leaf_index, root)
    logger.info("BVH built successfully")
    return bvh, order.astype(np.int32)


@njit(inline="always")
def _aabb_intersect(
    min_a: np.ndarray, max_a: np.ndarray, min_b: np.ndarray, max_b: np.ndarray
) -> bool:
    result = bool(np.all(min_a <= max_b) and np.all(max_a >= min_b))
    return result


@njit(cache=True)
def _enumerate_overlapping_pairs_kernel(
    left: np.ndarray,
    right: np.ndarray,
    leaf_index: np.ndarray,
    node_min: np.ndarray,
    node_max: np.ndarray,
    volumes: np.ndarray,
    n_leaves: int,
) -> np.ndarray:
    """Numba-optimized core traversal kernel for BVH overlap enumeration."""
    # Pre-allocate stack and pairs arrays
    # Worst case: O(n^2) pairs, but typically much smaller
    max_stack_size = n_leaves * 4  # Conservative estimate
    max_pairs = n_leaves * (n_leaves - 1) // 2  # Upper bound

    stack = np.empty((max_stack_size, 2), dtype=np.int32)
    pairs = np.empty((max_pairs, 2), dtype=np.int32)

    stack_size = 0
    pairs_size = 0

    # Seed stack with children of all internal nodes
    for i in range(n_leaves, 2 * n_leaves - 1):
        left_child = left[i]
        right_child = right[i]

        if left_child != -1 and right_child != -1:
            # Check if their bounding boxes overlap
            if _aabb_intersect(
                node_min[left_child],
                node_max[left_child],
                node_min[right_child],
                node_max[right_child],
            ):
                stack[stack_size, 0] = left_child
                stack[stack_size, 1] = right_child
                stack_size += 1

    leaf_cut = n_leaves

    # Main traversal loop
    while stack_size > 0:
        stack_size -= 1
        a = stack[stack_size, 0]
        b = stack[stack_size, 1]

        # Check AABB intersection
        if not _aabb_intersect(node_min[a], node_max[a], node_min[b], node_max[b]):
            continue

        a_is_leaf = a < leaf_cut
        b_is_leaf = b < leaf_cut

        # Both are leaves - record the pair
        if a_is_leaf and b_is_leaf:
            ia = leaf_index[a]
            ib = leaf_index[b]

            if ia != ib:
                if ia < ib:
                    pairs[pairs_size, 0] = ia
                    pairs[pairs_size, 1] = ib
                else:
                    pairs[pairs_size, 0] = ib
                    pairs[pairs_size, 1] = ia
                pairs_size += 1
            continue

        # Expand the larger-volume internal node
        if (not a_is_leaf) and (b_is_leaf or volumes[a] >= volumes[b]):
            stack[stack_size, 0] = left[a]
            stack[stack_size, 1] = b
            stack_size += 1
            stack[stack_size, 0] = right[a]
            stack[stack_size, 1] = b
            stack_size += 1
        else:
            stack[stack_size, 0] = a
            stack[stack_size, 1] = left[b]
            stack_size += 1
            stack[stack_size, 0] = a
            stack[stack_size, 1] = right[b]
            stack_size += 1

    # Return only the filled portion of pairs array
    return pairs[:pairs_size]


def enumerate_overlapping_pairs(bvh: LBVH) -> np.ndarray:
    logger.info(f"enumerate_overlapping_pairs called with root={bvh.root}")

    n_leaves = int(np.sum(bvh.leaf_index[: len(bvh.leaf_index)] >= 0))

    if bvh.root < 0 or n_leaves < 2:
        logger.info("No pairs to enumerate")
        return np.empty((0, 2), dtype=np.int32)

    # Precompute volumes for heuristic
    extents = np.maximum(bvh.node_max - bvh.node_min, 0.0)
    volumes = np.prod(extents, axis=1)

    # Call the optimized kernel
    arr = _enumerate_overlapping_pairs_kernel(
        bvh.left,
        bvh.right,
        bvh.leaf_index,
        bvh.node_min,
        bvh.node_max,
        volumes,
        n_leaves,
    )

    logger.info(f"Found {len(arr)} overlapping pairs")

    if arr.shape[0] == 0:
        return np.empty((0, 2), dtype=np.int32)

    # Deduplicate
    if arr.shape[0] > 1:
        view = arr.view([("a", arr.dtype), ("b", arr.dtype)])
        _, idx = np.unique(view, return_index=True)
        arr = arr[np.sort(idx)]

    logger.info(f"enumerate_overlapping_pairs returning {len(arr)} pairs")
    return arr
