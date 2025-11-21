from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
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


def _clz32(x: int) -> int:
    logger.debug(f"_clz32 called with x={x}")
    if x <= 0:
        # x == 0 -> 32 leading zeros for 32-bit
        logger.debug(f"_clz32 returning 32 for x={x}")
        return 32
    result = 32 - int(x).bit_length()
    logger.debug(f"_clz32 returning {result} for x={x}")
    return result


def _lcp(i: int, j: int, morton: np.ndarray, n: int) -> int:
    logger.debug(f"_lcp called with i={i}, j={j}, n={n}")
    if j < 0 or j >= n:
        logger.debug(f"_lcp returning -1 for i={i}, j={j} (out of bounds)")
        return -1
    a = int(morton[i])
    b = int(morton[j])
    if a == b:
        # Tie-breaker by index per Karras 2012
        result = 32 + _clz32(i ^ j)
        logger.debug(f"_lcp returning {result} for i={i}, j={j} (equal morton codes)")
        return result
    result = _clz32(a ^ b)
    logger.debug(f"_lcp returning {result} for i={i}, j={j} (different morton codes)")
    return result


def _expand_bits_2d(v: np.ndarray) -> np.ndarray:
    logger.debug(f"_expand_bits_2d called with v shape={v.shape}")
    # Interleave 16-bit to 32-bit (up to 10 bits used)
    x = v.astype(np.uint32)
    logger.debug(f"Initial x shape={x.shape}, values: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 8)) & np.uint32(0x00FF00FF)
    logger.debug(f"After first operation: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 4)) & np.uint32(0x0F0F0F0F)
    logger.debug(f"After second operation: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 2)) & np.uint32(0x33333333)
    logger.debug(f"After third operation: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 1)) & np.uint32(0x55555555)
    logger.debug(f"After fourth operation: {x[:5] if len(x) > 5 else x}")
    logger.debug(f"_expand_bits_2d returning shape={x.shape}")
    return x


def _morton2d(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    logger.debug(f"_morton2d called with x shape={x.shape}, y shape={y.shape}")
    xx = _expand_bits_2d(x)
    yy = _expand_bits_2d(y) << np.uint32(1)
    result = xx | yy
    logger.debug(f"_morton2d returning shape={result.shape}")
    return result


def _expand_bits_3d(v: np.ndarray) -> np.ndarray:
    logger.debug(f"_expand_bits_3d called with v shape={v.shape}")
    # Interleave 10-bit into 30-bit
    x = v.astype(np.uint32)
    logger.debug(f"Initial x shape={x.shape}, values: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 16)) & np.uint32(0x030000FF)
    logger.debug(f"After first operation: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 8)) & np.uint32(0x0300F00F)
    logger.debug(f"After second operation: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 4)) & np.uint32(0x030C30C3)
    logger.debug(f"After third operation: {x[:5] if len(x) > 5 else x}")
    x = (x | (x << 2)) & np.uint32(0x09249249)
    logger.debug(f"After fourth operation: {x[:5] if len(x) > 5 else x}")
    logger.debug(f"_expand_bits_3d returning shape={x.shape}")
    return x


def _morton3d(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    logger.debug(
        f"_morton3d called with x shape={x.shape}, y shape={y.shape}, z shape={z.shape}"
    )
    xx = _expand_bits_3d(x)
    yy = _expand_bits_3d(y) << np.uint32(1)
    zz = _expand_bits_3d(z) << np.uint32(2)
    result = xx | yy | zz
    logger.debug(f"_morton3d returning shape={result.shape}")
    return result


def _quantize01(vals: np.ndarray) -> np.ndarray:
    logger.debug(f"_quantize01 called with vals shape={vals.shape}")
    # Map [0,1] -> [0, 1023]
    clipped = np.clip(vals, 0.0, 1.0)
    logger.debug(f"Clipped values: {clipped[:5] if len(clipped) > 5 else clipped}")
    scaled = clipped * 1023.0
    logger.debug(f"Scaled values: {scaled[:5] if len(scaled) > 5 else scaled}")
    floored = np.floor(scaled)
    logger.debug(f"Floored values: {floored[:5] if len(floored) > 5 else floored}")
    result = floored.astype(np.int32)
    logger.debug(f"_quantize01 returning shape={result.shape}")
    return result


def _compute_morton_codes(
    centers: np.ndarray, bounds_min: np.ndarray, bounds_max: np.ndarray
) -> np.ndarray:
    logger.info(f"_compute_morton_codes called with centers shape={centers.shape}")
    n, d = centers.shape
    logger.debug(f"n={n}, d={d}")

    # Normalize to [0,1]
    size = np.maximum(bounds_max - bounds_min, 1e-12)
    logger.debug(f"Size computed: {size}")
    norm = (centers - bounds_min) / size
    logger.debug(f"Normalized centers shape={norm.shape}")

    if d >= 3:
        qx = _quantize01(norm[:, 0])
        qy = _quantize01(norm[:, 1])
        qz = _quantize01(norm[:, 2])
        logger.debug(f"Quantized values - qx: {qx[:5]}, qy: {qy[:5]}, qz: {qz[:5]}")
        result = _morton3d(qx, qy, qz).astype(np.uint32)
        logger.info(
            f"_compute_morton_codes returning 3D morton codes shape={result.shape}"
        )
    else:
        qx = _quantize01(norm[:, 0])
        qy = _quantize01(norm[:, 1])
        logger.debug(f"Quantized values - qx: {qx[:5]}, qy: {qy[:5]}")
        result = _morton2d(qx, qy).astype(np.uint32)
        logger.info(
            f"_compute_morton_codes returning 2D morton codes shape={result.shape}"
        )

    return result


def _find_split(first: int, last: int, morton: np.ndarray) -> int:
    logger.debug(f"_find_split called with first={first}, last={last}")
    # Karras 2012: find index where highest differing bit between first and last splits the range
    first_code = int(morton[first])
    last_code = int(morton[last])
    logger.debug(f"first_code={first_code}, last_code={last_code}")

    if first_code == last_code:
        result = (first + last) >> 1
        logger.debug(f"_find_split returning {result} (equal codes)")
        return result

    common_prefix = _clz32(first_code ^ last_code)
    logger.debug(f"Common prefix: {common_prefix}")

    split = first
    step = last - first
    logger.debug(f"Initial split={split}, step={step}")

    while step > 1:
        step = (step + 1) >> 1
        new_split = split + step
        logger.debug(f"Testing new_split={new_split}, step={step}")
        if new_split < last:
            split_code = int(morton[new_split])
            prefix = _clz32(first_code ^ split_code)
            logger.debug(f"Split code={split_code}, prefix={prefix}")
            if prefix > common_prefix:
                split = new_split
                logger.debug(f"Updated split to {split}")
    result = split
    logger.debug(f"_find_split returning {result}")
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
    logger.debug(f"n={n}")

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
    logger.debug(f"Building BVH for {n} leaves in {d} dimensions")

    centers = 0.5 * (aabb_min + aabb_max)
    logger.debug(f"Centers shape={centers.shape}")

    morton = _compute_morton_codes(centers, bounds_min[:d], bounds_max[:d])
    logger.debug(f"Morton codes shape={morton.shape}, first 5: {morton[:5]}")

    order = np.argsort(morton, kind="mergesort")  # stable sort
    logger.debug(f"Order shape={order.shape}, first 5: {order[:5]}")

    aabb_min_sorted = aabb_min[order]
    aabb_max_sorted = aabb_max[order]
    logger.debug(
        f"Sorted AABBs shapes: min={aabb_min_sorted.shape}, max={aabb_max_sorted.shape}"
    )

    # Node indexing: leaves [0..N-1], internals [N..2N-2]
    m = 2 * n - 1
    logger.debug(f"Total nodes: {m} (leaves: {n}, internals: {n - 1})")

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

    logger.debug(f"Initialized leaves: {n} nodes")

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
        logger.debug(f"build_subtree_recursive: first={first}, last={last}")

        if first == last:
            # Single leaf
            logger.debug(f"Leaf node: {first}")
            return first

        # Find split point
        split = _find_split(first, last, morton)
        logger.debug(f"Split: {split} (range [{first}, {last}])")

        # Recursively build left and right subtrees
        left_node = build_subtree_recursive(first, split)
        right_node = build_subtree_recursive(split + 1, last)

        # Allocate internal node
        this_node = n + next_internal_idx[0]
        next_internal_idx[0] += 1
        logger.debug(f"Internal node {this_node}: left={left_node}, right={right_node}")

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


def _aabb_intersect(
    min_a: np.ndarray, max_a: np.ndarray, min_b: np.ndarray, max_b: np.ndarray
) -> bool:
    logger.debug(
        f"_aabb_intersect called with shapes min_a={min_a.shape}, max_a={max_a.shape}"
    )
    result = bool(np.all(min_a <= max_b) and np.all(max_a >= min_b))
    logger.debug(f"_aabb_intersect returning {result}")
    return result


def enumerate_overlapping_pairs(bvh: LBVH) -> np.ndarray:
    logger.info(f"enumerate_overlapping_pairs called with root={bvh.root}")

    n_leaves = int(np.sum(bvh.leaf_index[: len(bvh.leaf_index)] >= 0))
    logger.debug(f"Number of leaves: {n_leaves}")

    if bvh.root < 0 or n_leaves < 2:
        logger.info("No pairs to enumerate")
        return np.empty((0, 2), dtype=np.int32)

    # Precompute volumes for heuristic
    extents = np.maximum(bvh.node_max - bvh.node_min, 0.0)
    volumes = np.prod(extents, axis=1)
    logger.debug(f"Volumes computed for {len(volumes)} nodes")

    pairs: list[tuple[int, int]] = []
    stack: list[tuple[int, int]] = []

    # FIX: Seed the stack with children of ALL internal nodes to cover all subtrees.
    # Internal nodes are stored at indices [n_leaves, 2*n_leaves - 2]
    for i in range(n_leaves, 2 * n_leaves - 1):
        left_child = int(bvh.left[i])
        right_child = int(bvh.right[i])

        # Only process valid internal nodes
        if left_child != -1 and right_child != -1:
            # Optimization: Only add to stack if their bounding boxes actually overlap
            if _aabb_intersect(
                bvh.node_min[left_child],
                bvh.node_max[left_child],
                bvh.node_min[right_child],
                bvh.node_max[right_child],
            ):
                stack.append((left_child, right_child))

    leaf_cut = n_leaves  # node id < leaf_cut -> leaf

    logger.info(f"Starting overlap enumeration with {len(stack)} initial pairs")

    while stack:
        a, b = stack.pop()
        logger.debug(f"Processing pair (a={a}, b={b})")

        if not _aabb_intersect(
            bvh.node_min[a], bvh.node_max[a], bvh.node_min[b], bvh.node_max[b]
        ):
            logger.debug(f"AABBs do not intersect, skipping pair (a={a}, b={b})")
            continue

        a_is_leaf = a < leaf_cut
        b_is_leaf = b < leaf_cut

        logger.debug(f"a_is_leaf={a_is_leaf}, b_is_leaf={b_is_leaf}")

        if a_is_leaf and b_is_leaf:
            ia = int(bvh.leaf_index[a])
            ib = int(bvh.leaf_index[b])
            logger.debug(f"Leaf pair found: ia={ia}, ib={ib}")

            if ia != ib:
                if ia < ib:
                    pairs.append((ia, ib))
                else:
                    pairs.append((ib, ia))
            continue

        # Expand the larger-volume internal node
        if (not a_is_leaf) and (b_is_leaf or volumes[a] >= volumes[b]):
            logger.debug(f"Expanding node a={a} (larger volume)")
            stack.append((int(bvh.left[a]), int(b)))
            stack.append((int(bvh.right[a]), int(b)))
        else:
            logger.debug(f"Expanding node b={b}")
            stack.append((int(a), int(bvh.left[b])))
            stack.append((int(a), int(bvh.right[b])))

    logger.info(f"Found {len(pairs)} overlapping pairs")

    if not pairs:
        return np.empty((0, 2), dtype=np.int32)

    arr = np.asarray(pairs, dtype=np.int32)
    # Deduplicate
    if arr.shape[0] > 1:
        logger.debug("Deduplicating pairs")
        view = arr.view([("a", arr.dtype), ("b", arr.dtype)])
        _, idx = np.unique(view, return_index=True)
        arr = arr[np.sort(idx)]
        logger.debug(f"After deduplication: {len(arr)} pairs")

    logger.info(f"enumerate_overlapping_pairs returning {len(arr)} pairs")
    return arr
