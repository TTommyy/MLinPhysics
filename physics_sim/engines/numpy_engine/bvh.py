from __future__ import annotations

from dataclasses import dataclass

import numpy as np


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
    if x <= 0:
        # x == 0 -> 32 leading zeros for 32-bit
        return 32
    return 32 - int(x).bit_length()


def _lcp(i: int, j: int, morton: np.ndarray, n: int) -> int:
    if j < 0 or j >= n:
        return -1
    a = int(morton[i])
    b = int(morton[j])
    if a == b:
        # Tie-breaker by index per Karras 2012
        return 32 + _clz32(i ^ j)
    return _clz32(a ^ b)


def _expand_bits_2d(v: np.ndarray) -> np.ndarray:
    # Interleave 16-bit to 32-bit (up to 10 bits used)
    x = v.astype(np.uint32)
    x = (x | (x << 8)) & np.uint32(0x00FF00FF)
    x = (x | (x << 4)) & np.uint32(0x0F0F0F0F)
    x = (x | (x << 2)) & np.uint32(0x33333333)
    x = (x | (x << 1)) & np.uint32(0x55555555)
    return x


def _morton2d(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    xx = _expand_bits_2d(x)
    yy = _expand_bits_2d(y) << np.uint32(1)
    return xx | yy


def _expand_bits_3d(v: np.ndarray) -> np.ndarray:
    # Interleave 10-bit into 30-bit
    x = v.astype(np.uint32)
    x = (x | (x << 16)) & np.uint32(0x030000FF)
    x = (x | (x << 8)) & np.uint32(0x0300F00F)
    x = (x | (x << 4)) & np.uint32(0x030C30C3)
    x = (x | (x << 2)) & np.uint32(0x09249249)
    return x


def _morton3d(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    xx = _expand_bits_3d(x)
    yy = _expand_bits_3d(y) << np.uint32(1)
    zz = _expand_bits_3d(z) << np.uint32(2)
    return xx | yy | zz


def _quantize01(vals: np.ndarray) -> np.ndarray:
    # Map [0,1] -> [0, 1023]
    q = np.floor(np.clip(vals, 0.0, 1.0) * 1023.0).astype(np.int32)
    return q


def _compute_morton_codes(
    centers: np.ndarray, bounds_min: np.ndarray, bounds_max: np.ndarray
) -> np.ndarray:
    n, d = centers.shape
    # Normalize to [0,1]
    size = np.maximum(bounds_max - bounds_min, 1e-12)
    norm = (centers - bounds_min) / size

    if d >= 3:
        qx = _quantize01(norm[:, 0])
        qy = _quantize01(norm[:, 1])
        qz = _quantize01(norm[:, 2])
        return _morton3d(qx, qy, qz).astype(np.uint32)
    else:
        qx = _quantize01(norm[:, 0])
        qy = _quantize01(norm[:, 1])
        return _morton2d(qx, qy).astype(np.uint32)


def _find_split(first: int, last: int, morton: np.ndarray) -> int:
    # Karras 2012: find index where highest differing bit between first and last splits the range
    first_code = int(morton[first])
    last_code = int(morton[last])
    if first_code == last_code:
        return (first + last) >> 1

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
    return split


def build_lbvh(
    aabb_min: np.ndarray,
    aabb_max: np.ndarray,
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
) -> tuple[LBVH, np.ndarray]:
    """
    Build a Linear BVH from leaf AABBs.

    Returns (LBVH, leaf_order), where leaf_order maps leaf id -> original collider index.
    """
    n = int(aabb_min.shape[0])
    if n == 0:
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
    centers = 0.5 * (aabb_min + aabb_max)
    morton = _compute_morton_codes(centers, bounds_min[:d], bounds_max[:d])

    order = np.argsort(morton, kind="mergesort")  # stable sort
    aabb_min_sorted = aabb_min[order]
    aabb_max_sorted = aabb_max[order]

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
        return bvh, order.astype(np.int32)

    # Precompute LCP accessor in local scope
    def lcp(i: int, j: int) -> int:
        return _lcp(i, j, morton, n)

    # Build internal nodes
    for i in range(n - 1):
        # Determine range direction
        lcp_next = lcp(i, i + 1)
        lcp_prev = lcp(i, i - 1)
        direction = 1 if lcp_next > lcp_prev else -1

        # Find range length by exponential search
        delta_min = lcp(i, i - direction)
        lmax = 2
        while True:
            j = i + lmax * direction
            if j < 0 or j >= n or lcp(i, j) <= delta_min:
                break
            lmax <<= 1

        # Binary search to find other end j
        bound = 0
        step = lmax
        while step > 1:
            step = (step + 1) >> 1
            j = i + (bound + step) * direction
            if 0 <= j < n and lcp(i, j) > delta_min:
                bound += step
        j = i + bound * direction

        first = min(i, j)
        last = max(i, j)
        split = _find_split(first, last, morton)

        # Determine children (leaf or internal)
        left_child = split
        right_child = split + 1

        # Map to node indices
        left_node = left_child if left_child == first else (n + left_child)
        right_node = right_child if right_child == last else (n + right_child)

        this_node = n + i
        left[this_node] = left_node
        right[this_node] = right_node
        parent[left_node] = this_node
        parent[right_node] = this_node

    # Find root (the only internal node without parent)
    root = int(np.where((parent[n:] == -1))[0][0] + n)

    # Post-order traversal to compute internal AABBs
    stack = [root]
    postorder: list[int] = []
    while stack:
        node = stack.pop()
        postorder.append(node)
        l = left[node]
        r = right[node]
        if l != -1:
            stack.append(l)
        if r != -1:
            stack.append(r)

    for node in reversed(postorder):
        l = left[node]
        r = right[node]
        if l == -1 and r == -1:
            continue  # leaf already has AABB
        if l != -1:
            node_min[node] = (
                np.minimum(node_min[node], node_min[l])
                if node_min[node].any()
                else node_min[l]
            )
            node_max[node] = (
                np.maximum(node_max[node], node_max[l])
                if node_max[node].any()
                else node_max[l]
            )
        if r != -1:
            node_min[node] = (
                np.minimum(node_min[node], node_min[r])
                if node_min[node].any()
                else node_min[r]
            )
            node_max[node] = (
                np.maximum(node_max[node], node_max[r])
                if node_max[node].any()
                else node_max[r]
            )

    bvh = LBVH(left, right, parent, node_min, node_max, leaf_index, root)
    return bvh, order.astype(np.int32)


def _aabb_intersect(
    min_a: np.ndarray, max_a: np.ndarray, min_b: np.ndarray, max_b: np.ndarray
) -> bool:
    return bool(np.all(min_a <= max_b) and np.all(max_a >= min_b))


def enumerate_overlapping_pairs(bvh: LBVH) -> np.ndarray:
    n_leaves = int(np.sum(bvh.leaf_index[: len(bvh.leaf_index)] >= 0))
    if bvh.root < 0 or n_leaves == 0:
        return np.empty((0, 2), dtype=np.int32)

    # Precompute volumes for heuristic
    extents = np.maximum(bvh.node_max - bvh.node_min, 0.0)
    volumes = np.prod(extents, axis=1)

    pairs: list[tuple[int, int]] = []
    stack: list[tuple[int, int]] = []
    l_root = bvh.left[bvh.root]
    r_root = bvh.right[bvh.root]
    if l_root == -1 or r_root == -1:
        return np.empty((0, 2), dtype=np.int32)
    stack.append((l_root, r_root))

    leaf_cut = n_leaves  # node id < leaf_cut -> leaf

    while stack:
        a, b = stack.pop()
        if not _aabb_intersect(
            bvh.node_min[a], bvh.node_max[a], bvh.node_min[b], bvh.node_max[b]
        ):
            continue

        a_is_leaf = a < leaf_cut
        b_is_leaf = b < leaf_cut

        if a_is_leaf and b_is_leaf:
            ia = int(bvh.leaf_index[a])
            ib = int(bvh.leaf_index[b])
            if ia != ib:
                if ia < ib:
                    pairs.append((ia, ib))
                else:
                    pairs.append((ib, ia))
            continue

        # Expand the larger-volume internal node
        if (not a_is_leaf) and (b_is_leaf or volumes[a] >= volumes[b]):
            stack.append((bvh.left[a], b))
            stack.append((bvh.right[a], b))
        else:
            stack.append((a, bvh.left[b]))
            stack.append((a, bvh.right[b]))

    if not pairs:
        return np.empty((0, 2), dtype=np.int32)

    arr = np.asarray(pairs, dtype=np.int32)
    # Deduplicate
    if arr.shape[0] > 1:
        view = arr.view([("a", arr.dtype), ("b", arr.dtype)])
        _, idx = np.unique(view, return_index=True)
        arr = arr[np.sort(idx)]
    return arr
