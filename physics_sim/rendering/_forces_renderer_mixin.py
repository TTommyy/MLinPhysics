import math
from typing import Any

import arcade
import numpy as np


class ForcesRendererMixin:
    """Mixin to render forces as a vector field and overlays."""

    def __init__(self, *args, **kwargs):
        # Cooperative init to play nice in MRO
        super().__init__(*args, **kwargs)
        # Defaults specific to this mixin
        self._force_field_include_minor: bool = True
        self._force_field_spacing_override: float | None = None


    def set_force_field_include_minor(self, include_minor: bool) -> None:
        self._force_field_include_minor = include_minor

    def set_force_field_spacing(self, spacing: float | None) -> None:
        self._force_field_spacing_override = spacing

    def _draw_vector_field(
        self, sample_points: np.ndarray, vectors: np.ndarray, spacing: float
    ) -> None:
        if len(sample_points) == 0:
            return
        # Scale vectors to a reasonable on-screen length
        max_len = 0.35 * spacing
        # Compute a normalization factor based on magnitudes
        mags = np.linalg.norm(vectors, axis=1)
        if np.all(mags == 0):
            return
        scale = max_len / (np.max(mags) + 1e-9)

        color = (50, 90, 200)
        thickness = 2

        for (px, py), vec in zip(sample_points, vectors):
            sx = self.physics_to_screen_x(px)
            sy = self.physics_to_screen_y(py)
            ex = self.physics_to_screen_x(px + vec[0] * scale)
            ey = self.physics_to_screen_y(py + vec[1] * scale)
            arcade.draw_line(sx, sy, ex, ey, color, thickness)

    def _draw_overlays(self, overlays: list[dict[str, Any]]) -> None:
        for item in overlays:
            kind = item.get("kind")
            if kind == "circle":
                x, y = item["position"]
                r = float(item["radius"]) * self.scale
                sx = self.physics_to_screen_x(x)
                sy = self.physics_to_screen_y(y)
                color = item.get("color", (80, 80, 80))
                arcade.draw_circle_outline(sx, sy, r, color, 2)
            elif kind == "text":
                x, y = item["position"]
                sx = self.physics_to_screen_x(x)
                sy = self.physics_to_screen_y(y)
                text = str(item.get("text", ""))
                color = item.get("color", (30, 30, 30))
                size = int(item.get("size", 10))
                arcade.Text(text, sx + 6, sy + 6, color, size, bold=True).draw()
            elif kind == "dashed_circle":
                x, y = item["position"]
                radius_world = float(item["radius"])
                sx = self.physics_to_screen_x(x)
                sy = self.physics_to_screen_y(y)
                radius_px = radius_world * self.scale
                color = item.get("color", (80, 80, 80))
                # Draw dashed circle by short arc segments
                segments = 64
                dash_on = True
                for i in range(segments):
                    a0 = (2 * math.pi * i) / segments
                    a1 = (2 * math.pi * (i + 1)) / segments
                    if dash_on:
                        x0 = sx + radius_px * math.cos(a0)
                        y0 = sy + radius_px * math.sin(a0)
                        x1 = sx + radius_px * math.cos(a1)
                        y1 = sy + radius_px * math.sin(a1)
                        arcade.draw_line(x0, y0, x1, y1, color, 2)
                    dash_on = not dash_on

    def render_forces(self, forces: list) -> None:
        if not getattr(self, "show_forces", False):
            return
        # Sample points aligned with grid
        points_list = self.get_grid_sample_points(
            include_minor=self._force_field_include_minor,
            custom_spacing=self._force_field_spacing_override,
        )
        if not points_list:
            return
        sample_points = np.asarray(points_list, dtype=np.float64)

        # Sum vector contributions
        accumulated = np.zeros_like(sample_points)
        overlays: list[dict[str, Any]] = []
        for f in forces:
            try:
                rd = f.get_render_data(sample_points)
            except Exception:
                rd = {}
            if not isinstance(rd, dict):
                continue
            vf = rd.get("vector_field")
            if isinstance(vf, np.ndarray) and vf.shape == accumulated.shape:
                accumulated += vf
            ov = rd.get("overlays")
            if isinstance(ov, list):
                overlays.extend(ov)

        # Estimate spacing to scale vectors
        spacing = self._force_field_spacing_override
        if spacing is None:
            spacing = self._calculate_grid_spacing(1)

        self._draw_vector_field(sample_points, accumulated, spacing)
        if overlays:
            self._draw_overlays(overlays)
