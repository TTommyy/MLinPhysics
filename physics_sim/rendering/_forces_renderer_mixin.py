import logging
import math
from typing import Any

import numpy as np
from kivy.graphics import Color, InstructionGroup, Line, Rectangle, Triangle

from physics_sim.ui.utils import color_to_rgba, format_numbers_in_text

logger = logging.getLogger(__name__)

# Vector field rendering constants (avoid magic numbers)
VECTOR_MAX_LENGTH_RATIO: float = 0.40  # fraction of grid spacing
VECTOR_COLOR_LOW: tuple[int, int, int] = (50, 90, 200)
VECTOR_COLOR_HIGH: tuple[int, int, int] = (230, 60, 60)
ARROW_HEAD_MIN_PX: float = 4.0
ARROW_HEAD_MAX_PX: float = 28.0
ARROW_HEAD_WIDTH_RATIO: float = 0.8  # head width relative to head length


def _lerp_color(c0, c1, t: float) -> tuple[int, int, int]:
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(3))


class ForcesRendererMixin:
    """Mixin to render forces as a vector field and overlays on a Kivy canvas."""

    forces_group: InstructionGroup

    def _init_forces_renderer(self) -> None:
        self._force_field_include_minor: bool = True
        self._force_field_spacing_override: float | None = None
        self._forces_cache_key: tuple | None = None

    def set_force_field_include_minor(self, include_minor: bool) -> None:
        self._force_field_include_minor = include_minor
        self._forces_cache_key = None

    def set_force_field_spacing(self, spacing: float | None) -> None:
        self._force_field_spacing_override = spacing
        self._forces_cache_key = None

    def invalidate_forces(self) -> None:
        self._forces_cache_key = None

    def clear_forces(self) -> None:
        """Remove any drawn force visualisation."""
        self.forces_group.clear()
        self._forces_cache_key = None

    def _draw_vector_field(
        self, sample_points: np.ndarray, vectors: np.ndarray, spacing: float
    ) -> None:
        if len(sample_points) == 0:
            return
        max_len = VECTOR_MAX_LENGTH_RATIO * spacing
        mags = np.linalg.norm(vectors, axis=1)
        if np.all(mags == 0) or not np.all(np.isfinite(mags)):
            finite = np.isfinite(mags)
            if not finite.any() or np.all(mags[finite] == 0):
                return
            vectors = np.where(finite[:, None], vectors, 0.0)
            mags = np.where(finite, mags, 0.0)
        max_mag = float(np.max(mags))
        scale = max_len / (max_mag + 1e-9)
        group = self.forces_group

        for (px, py), vec, mag in zip(sample_points, vectors, mags):
            if mag <= 0:
                continue
            strength = float(mag / (max_mag + 1e-9))
            group.add(Color(*color_to_rgba(_lerp_color(VECTOR_COLOR_LOW, VECTOR_COLOR_HIGH, strength))))

            sx = self.physics_to_screen_x(float(px))
            sy = self.physics_to_screen_y(float(py))
            ex = self.physics_to_screen_x(float(px + vec[0] * scale))
            ey = self.physics_to_screen_y(float(py + vec[1] * scale))
            group.add(Line(points=[sx, sy, ex, ey], width=1.0))

            dx, dy = ex - sx, ey - sy
            seg_len = math.hypot(dx, dy)
            if seg_len <= 1e-6:
                continue
            head_len = max(ARROW_HEAD_MIN_PX, min(ARROW_HEAD_MAX_PX, seg_len * 0.35))
            head_w = head_len * ARROW_HEAD_WIDTH_RATIO
            ux, uy = dx / seg_len, dy / seg_len
            bx, by = ex - ux * head_len, ey - uy * head_len
            ox, oy = -uy * (head_w * 0.5), ux * (head_w * 0.5)
            group.add(Triangle(points=[ex, ey, bx + ox, by + oy, bx - ox, by - oy]))

    def _draw_overlays(self, overlays: list[dict[str, Any]]) -> None:
        group = self.forces_group
        for item in overlays:
            kind = item.get("kind")
            try:
                x, y = item["position"]
            except (KeyError, TypeError, ValueError):
                continue
            sx = self.physics_to_screen_x(float(x))
            sy = self.physics_to_screen_y(float(y))
            if kind == "circle":
                r = float(item["radius"]) * self.scale
                group.add(Color(*color_to_rgba(item.get("color", (80, 80, 80)))))
                group.add(Line(circle=(sx, sy, max(r, 1.0)), width=1.5))
            elif kind == "text":
                text = format_numbers_in_text(str(item.get("text", "")))
                color = color_to_rgba(item.get("color", (30, 30, 30)))
                size = float(item.get("size", 10)) + 2
                texture = self._text_cache.get(text, size, color, True)
                group.add(Color(1, 1, 1, 1))
                group.add(Rectangle(texture=texture, size=texture.size, pos=(sx, sy)))
            elif kind == "dashed_circle":
                radius_px = float(item["radius"]) * self.scale
                group.add(Color(*color_to_rgba(item.get("color", (80, 80, 80)))))
                segments = 64
                for i in range(0, segments, 2):
                    a0 = (2 * math.pi * i) / segments
                    a1 = (2 * math.pi * (i + 1)) / segments
                    group.add(
                        Line(
                            points=[
                                sx + radius_px * math.cos(a0),
                                sy + radius_px * math.sin(a0),
                                sx + radius_px * math.cos(a1),
                                sy + radius_px * math.sin(a1),
                            ],
                            width=1.5,
                        )
                    )

    def _field_spacing(self) -> float:
        spacing = self._force_field_spacing_override
        if spacing is None:
            spacing = self._calculate_grid_spacing(1)
        return spacing

    def render_forces(self, forces: list) -> None:
        """Render forces by querying them directly (no engine involved)."""
        if not getattr(self, "show_forces", False):
            self.clear_forces()
            return
        points_list = self.get_grid_sample_points(
            include_minor=self._force_field_include_minor,
            custom_spacing=self._force_field_spacing_override,
        )
        if not points_list:
            return
        sample_points = np.asarray(points_list, dtype=np.float64)
        accumulated = np.zeros_like(sample_points)
        overlays: list[dict[str, Any]] = []
        for f in forces:
            try:
                rd = f.get_render_data(sample_points)
            except Exception as e:
                logger.warning("Force %s get_render_data failed: %s", f.name, e)
                rd = {}
            if not isinstance(rd, dict):
                continue
            vf = rd.get("vector_field")
            if isinstance(vf, np.ndarray) and vf.shape == accumulated.shape:
                accumulated += vf
            ov = rd.get("overlays")
            if isinstance(ov, list):
                overlays.extend(ov)
        self.forces_group.clear()
        self._forces_cache_key = None
        self._draw_vector_field(sample_points, accumulated, self._field_spacing())
        if overlays:
            self._draw_overlays(overlays)

    def render_forces_data(self, data: dict | None) -> None:
        """Render precomputed engine force data (vector field + overlays).

        Canvas instructions are only rebuilt when the data object or the
        viewport geometry changes.
        """
        if not self.show_forces or not data:
            if self._forces_cache_key is not None or len(self.forces_group.children):
                self.clear_forces()
            return

        key = (
            id(data),
            float(self.scale),
            float(self.region.left),
            float(self.region.bottom),
            float(self.region.width),
            float(self.region.height),
        )
        if key == self._forces_cache_key:
            return
        self._forces_cache_key = key
        self.forces_group.clear()

        vectors = data.get("vector_field")
        overlays = data.get("overlays", [])
        points_list = self.get_grid_sample_points()
        if points_list:
            sample_points = np.asarray(points_list, dtype=np.float64)
            if isinstance(vectors, np.ndarray) and vectors.shape == sample_points.shape:
                self._draw_vector_field(sample_points, vectors, self._field_spacing())
        if isinstance(overlays, list) and overlays:
            self._draw_overlays(overlays)
