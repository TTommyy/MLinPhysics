# LBVH Broad-Phase for NumPy Engine (dimension-agnostic)

## Scope and constraints

- Rebuild BVH every step; handle all colliders (balls + obstacles).
- Dimension-agnostic arrays: infer D from `self._positions.shape[1]`; support Morton LBVH for D in {2,3}; generic AABB math for any D.
- Target scale >50k dynamic entities; avoid Python objects in hot paths.

## Algorithm overview

- Broad-phase: Linear BVH (LBVH) built from Morton codes (Karras 2012).
  - Compute per-entity AABBs and centers; normalize to world bounds; encode Morton codes (2D/3D).
  - Stable sort entities by code; build a binary tree using longest-common-prefix (LCP) to connect internal nodes in O(n).
  - Bottom-up compute internal node AABBs from children.
- Pair generation: stack-based node-pair traversal starting from (root.left, root.right).
  - If AABBs intersect: descend; emit a pair when both nodes are leaves.
  - Outputs unique overlapping AABB pairs in O(P + visits), P = candidate pairs.
- Narrow-phase: reuse existing resolution code, refactored to accept pair lists and run vectorized.

## Data model and memory layout

- AABBs: `aabb_min: (N, D)`, `aabb_max: (N, D)` computed from positions + half-extents per type.
- Tree (M = 2N-1 nodes):
  - `left, right, parent: (M,) int32` (−1 for leaf child absent)
  - `node_min, node_max: (M, D) float64`
  - `leaf_index: (M,) int32` (engine index for leaves; −1 for internals)
  - `root_index: int`
- Mapping arrays:
  - `leaf_to_engine_index: (N,) int32`, `leaf_to_type: (N,) int8`

## Build pipeline per step

1. Gather colliders and compute AABBs (vectorized):

   - BALL: radius -> `half = r` (repeat D), min = pos − half, max = pos + half.
   - RECTANGLE_OBSTACLE: half = (w/2, h/2, [zeros if D>2]).
   - CIRCLE_OBSTACLE: same as BALL, half = r.

2. Morton encoding (D ∈ {2,3}): normalize centers to [0,1]^D using simulation bounds; interleave bits to 30-bit (2D) or 30-bit per axis (3D).

   - Fallback for D>3: use first 3 components; AABB tests remain fully D-agnostic.

3. `argsort` Morton codes (stable) to get permutation; reorder AABBs and mappings.
4. Build internal nodes via LCP method (O(N)) and compute `node_min/max` bottom-up.
5. Return `LBVH` struct.

## Pair generation

- Use node-pair traversal:
  - Stack of `(i, j)`; init (left(root), right(root)).
  - While stack not empty:
    - If `intersect(node_i, node_j)` across all D:
      - If both leaves: emit `(leaf_to_engine[i], leaf_to_engine[j])` with `i<j`.
      - Else descend by expanding internal nodes against the other.
- Output three typed lists by filtering pairs using `leaf_to_type`.

## Integration into engine

- New files:
  - `physics_sim/engines/numpy_engine/bvh.py`: LBVH builder and traversal; pure NumPy.
  - `physics_sim/engines/numpy_engine/broadphase_mixin.py`: orchestrates AABB build, BVH build, and pair generation.
- Edits:
  - `engine.py::step`: after `_apply_constraints`, call `_build_bvh_and_pairs()`; pass pairs to narrow-phase resolvers.
  - `collision_mixin.py`: split into vectorized resolvers that accept pair arrays:
    - `_resolve_ball_ball_pairs(pairs)`
    - `_resolve_ball_rect_pairs(pairs)`
    - `_resolve_ball_circle_pairs(pairs)`

## Key function signatures (proposed)

```python
# bvh.py
@dataclass
class LBVH:
    left: np.ndarray; right: np.ndarray; parent: np.ndarray
    node_min: np.ndarray; node_max: np.ndarray
    leaf_index: np.ndarray; root: int

def build_lbvh(aabb_min: np.ndarray, aabb_max: np.ndarray, bounds_min: np.ndarray, bounds_max: np.ndarray) -> tuple[LBVH, np.ndarray]:
    """Returns (bvh, leaf_order) where leaf_order maps leaf slot -> original collider index."""

def enumerate_overlapping_pairs(bvh: LBVH) -> np.ndarray:
    """Returns (K,2) int32 unique overlapping leaf index pairs (leaf ids)."""
```

```python

# broadphase_mixin.py

class BroadphaseMixin:

def _build_bvh_and_pairs(self) -> dict[str, np.ndarray]:

"""Build AABBs for all colliders, build BVH, enumerate pairs, split by type."""

````
```python
# collision_mixin.py (new entrypoint)
def _resolve_with_pairs(self, pairs_by_type: dict[str, np.ndarray]) -> None:
    self._resolve_ball_ball_pairs(pairs_by_type["ball_ball"])  # vectorized
    self._resolve_ball_rect_pairs(pairs_by_type["ball_rect"])  # vectorized
    self._resolve_ball_circle_pairs(pairs_by_type["ball_circle"])  # vectorized
````

## Vectorized narrow-phase (reasoning)

- Converting from O(n^2) nested loops to per-pair vector ops reduces Python overhead and uses BLAS-friendly array math.
- For ball-ball: gather arrays by pairs `(i,j)` with `take`/advanced indexing; compute deltas, distances, masks; write back via scatter to both `i` and `j` (resolve with per-pair impulses and position corrections). Use `np.add.at` to accumulate symmetric updates safely.
- For ball-rect and ball-circle: compute contact normals/overlaps per pair; apply restitution and optional friction, as in current logic.

## Complexity and performance notes

- Build: Morton (O(N)), sort (O(N log N) via NumPy), connect nodes (O(N)). For 50k, this is typically <5–10 ms on modern CPUs; optimize later with radix sort if needed.
- Pair enumeration: near O(P) where P is broad-phase overlap count; usually sub-quadratic.
- Memory: M ≈ 2N nodes; for D=2, roughly a few MB at N=50k.

## Edge cases and robustness

- Degenerate AABBs (zero size) handled via EPS expansion when normalizing.
- Identical Morton codes: break ties via original index; stable sort preserves order; LCP code handles equal ranges.
- Bounds normalization: use engine `bounds`; clamp positions to [min,max] to keep codes finite.

## Optional future improvements

- Radix sort for Morton codes to reach O(N) sort.
- Two-level BVH: static (obstacles) cached, dynamic (balls) rebuilt; then merge nodes at top.
- SIMD-friendly traversal batches or packet traversal per cache line.
