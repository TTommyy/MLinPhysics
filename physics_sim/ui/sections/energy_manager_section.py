import arcade

from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection


class EnergyManagerSection(BaseSection):
    """Bottom panel section displaying energy plots."""

    def __init__(self, region: LayoutRegion, max_history: int = 300):
        super().__init__(
            region,
            background_color=(240, 240, 250),
            border_color=arcade.color.GRAY,
        )

        self.max_history = max_history

        # Energy history
        self.kinetic_history: list[float] = []
        self.potential_history: list[float] = []
        self.total_history: list[float] = []
        self.time_history: list[float] = []

        # Plot area (with margins)
        self.plot_margin_left = 60
        self.plot_margin_right = 30
        self.plot_margin_top = 40
        self.plot_margin_bottom = 40

        # Text objects
        self._create_text_objects()

        # Cached shapes for static elements
        self._plot_cache_key = None
        self._plot_shapes_static = None  # border + grid lines

        # Cached shapes for dynamic series
        self._series_cache_key = None
        self._series_shape_ke = None
        self._series_shape_pe = None
        self._series_shape_total = None

    def _create_text_objects(self):
        """Create reusable text objects."""
        x = self.region.x + 15
        y = self.region.top - 20

        self.title_text = arcade.Text(
            "ENERGY TRACKING",
            x,
            y,
            arcade.color.DARK_BLUE,
            14,
            bold=True,
        )

        # Legend texts (will be positioned dynamically)
        self.ke_legend_text = arcade.Text(
            "",
            0,
            0,
            arcade.uicolor.BLUE_PETER_RIVER,
            10,
            bold=True,
        )
        self.pe_legend_text = arcade.Text(
            "",
            0,
            0,
            arcade.uicolor.RED_POMEGRANATE,
            10,
            bold=True,
        )
        self.total_legend_text = arcade.Text(
            "",
            0,
            0,
            arcade.uicolor.GREEN_NEPHRITIS,
            10,
            bold=True,
        )

        # Axis labels
        self.x_axis_label = arcade.Text(
            "Time (s)",
            self.region.center_x,
            self.region.bottom + 15,
            arcade.color.BLACK,
            9,
            anchor_x="center",
        )
        self.y_axis_label = arcade.Text(
            "Energy (J)",
            self.region.x + 20,
            self.region.center_y,
            arcade.color.BLACK,
            9,
            anchor_x="center",
            rotation=90,
        )

    def add_energy_sample(self, ke: float, pe: float, total: float, time: float):
        """Add an energy sample to history.

        Args:
            ke: Kinetic energy in Joules
            pe: Potential energy in Joules
            total: Total energy in Joules
            time: Simulation time in seconds
        """
        self.kinetic_history.append(ke)
        self.potential_history.append(pe)
        self.total_history.append(total)
        self.time_history.append(time)

        # Limit history size
        if len(self.time_history) > self.max_history:
            self.kinetic_history.pop(0)
            self.potential_history.pop(0)
            self.total_history.pop(0)
            self.time_history.pop(0)

    def on_draw(self):
        """Draw the energy manager section."""
        self.draw_background()
        self.draw_border()

        # Draw title
        self.title_text.draw()

        # Draw plot if we have data
        if len(self.time_history) >= 2:
            self._render_energy_plot()

        # Draw axis labels
        self.x_axis_label.draw()
        self.y_axis_label.draw()

    def _render_energy_plot(self):
        """Render the energy plot with grid and legend."""
        if len(self.time_history) < 2:
            return

        # Calculate plot bounds
        plot_left = self.region.left + self.plot_margin_left
        plot_right = self.region.right - self.plot_margin_right
        plot_bottom = self.region.bottom + self.plot_margin_bottom
        plot_top = self.region.top - self.plot_margin_top

        plot_width = plot_right - plot_left
        plot_height = plot_top - plot_bottom

        if plot_width <= 0 or plot_height <= 0:
            return

        # Build/reuse static plot shapes (border + grid)
        key_static = (plot_left, plot_right, plot_bottom, plot_top)
        if key_static != self._plot_cache_key:
            self._plot_cache_key = key_static
            shapes = arcade.shape_list.ShapeElementList()
            # Border
            shapes.append(
                arcade.shape_list.create_rectangle_outline(
                    (plot_left + plot_right) * 0.5,
                    (plot_bottom + plot_top) * 0.5,
                    float(plot_right - plot_left),
                    float(plot_top - plot_bottom),
                    arcade.color.GRAY,
                    2,
                )
            )
            # Horizontal grid
            num_h_lines = 5
            h_points: list[tuple[float, float]] = []
            h_colors: list[tuple[int, int, int, int]] = []
            for i in range(num_h_lines + 1):
                y = plot_bottom + (plot_height * i / num_h_lines)
                h_points.extend([(plot_left, y), (plot_right, y)])
                h_colors.extend([(200, 200, 200, 255), (200, 200, 200, 255)])
            if h_points:
                shapes.append(
                    arcade.shape_list.create_lines_with_colors(h_points, h_colors, 1)
                )
            # Vertical grid
            num_v_lines = 6
            v_points: list[tuple[float, float]] = []
            v_colors: list[tuple[int, int, int, int]] = []
            for i in range(num_v_lines + 1):
                x = plot_left + (plot_width * i / num_v_lines)
                v_points.extend([(x, plot_bottom), (x, plot_top)])
                v_colors.extend([(200, 200, 200, 255), (200, 200, 200, 255)])
            if v_points:
                shapes.append(
                    arcade.shape_list.create_lines_with_colors(v_points, v_colors, 1)
                )
            self._plot_shapes_static = shapes

        if self._plot_shapes_static is not None:
            self._plot_shapes_static.draw()

        # Calculate data ranges
        time_min = min(self.time_history)
        time_max = max(self.time_history)
        time_range = time_max - time_min if time_max > time_min else 1.0

        # Find energy range (with some padding)
        all_energies = (
            self.kinetic_history + self.potential_history + self.total_history
        )
        energy_min = min(all_energies)
        energy_max = max(all_energies)
        energy_range = energy_max - energy_min if energy_max > energy_min else 1.0
        energy_padding = energy_range * 0.1
        energy_min -= energy_padding
        energy_max += energy_padding
        energy_range = energy_max - energy_min

        # Y-axis labels (text objects only)
        num_h_lines = 5
        for i in range(num_h_lines + 1):
            y = plot_bottom + (plot_height * i / num_h_lines)
            energy_value = energy_min + (energy_range * i / num_h_lines)
            arcade.Text(
                f"{energy_value:.1f}",
                plot_left - 5,
                y - 5,
                arcade.color.BLACK,
                8,
                anchor_x="right",
            ).draw()

        # X-axis labels (text objects only)
        num_v_lines = 6
        for i in range(num_v_lines + 1):
            x = plot_left + (plot_width * i / num_v_lines)
            if i % 2 == 0:
                time_value = time_min + (time_range * i / num_v_lines)
                arcade.Text(
                    f"{time_value:.1f}",
                    x,
                    plot_bottom - 15,
                    arcade.color.BLACK,
                    8,
                    anchor_x="center",
                ).draw()

        # Helper function to convert data to screen coordinates
        def to_screen_coords(time_val: float, energy_val: float) -> tuple[float, float]:
            x = plot_left + ((time_val - time_min) / time_range) * plot_width
            y = plot_bottom + ((energy_val - energy_min) / energy_range) * plot_height
            return x, y

        # Build/reuse dynamic series shapes (recreate if vertex count changed)
        def build_series(
            points_color: tuple[int, int, int, int],
            times: list[float],
            vals: list[float],
        ):
            pts: list[tuple[float, float]] = []
            cols: list[tuple[int, int, int, int]] = []
            for i in range(len(times) - 1):
                x1, y1 = to_screen_coords(times[i], vals[i])
                x2, y2 = to_screen_coords(times[i + 1], vals[i + 1])
                pts.extend([(x1, y1), (x2, y2)])
                cols.extend([points_color, points_color])
            return pts, cols

        key_series = (len(self.time_history),)
        if key_series != self._series_cache_key:
            self._series_cache_key = key_series

            def _rgba(color_like: tuple | list) -> tuple[int, int, int, int]:
                vals = tuple(color_like)
                if len(vals) == 3:
                    return (int(vals[0]), int(vals[1]), int(vals[2]), 255)
                if len(vals) == 4:
                    return (int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3]))
                # Fallback to black
                return (0, 0, 0, 255)

            blue = _rgba(arcade.uicolor.BLUE_PETER_RIVER)
            red = _rgba(arcade.uicolor.RED_POMEGRANATE)
            green = _rgba(arcade.uicolor.GREEN_NEPHRITIS)

            ke_pts, ke_cols = build_series(
                blue, self.time_history, self.kinetic_history
            )
            pe_pts, pe_cols = build_series(
                red, self.time_history, self.potential_history
            )
            tot_pts, tot_cols = build_series(
                green, self.time_history, self.total_history
            )

            self._series_shape_ke = (
                arcade.shape_list.create_lines_with_colors(ke_pts, ke_cols, 1)
                if ke_pts
                else None
            )
            self._series_shape_pe = (
                arcade.shape_list.create_lines_with_colors(pe_pts, pe_cols, 1)
                if pe_pts
                else None
            )
            self._series_shape_total = (
                arcade.shape_list.create_lines_with_colors(tot_pts, tot_cols, 1)
                if tot_pts
                else None
            )
        else:
            # Update data in-place
            def update_shape(shape, times: list[float], vals: list[float]):
                if shape is None:
                    return
                data: list[float] = []
                for i in range(len(times) - 1):
                    x1, y1 = to_screen_coords(times[i], vals[i])
                    x2, y2 = to_screen_coords(times[i + 1], vals[i + 1])
                    cr, cg, cb, ca = shape.colors[0]
                    data.extend([x1, y1, cr, cg, cb, ca, x2, y2, cr, cg, cb, ca])
                from array import array as _array

                shape.data = _array("f", data)
                if shape.geometry is not None:
                    shape.buffer.write(shape.data)

            update_shape(self._series_shape_ke, self.time_history, self.kinetic_history)
            update_shape(
                self._series_shape_pe, self.time_history, self.potential_history
            )
            update_shape(
                self._series_shape_total, self.time_history, self.total_history
            )

        if self._series_shape_ke:
            self._series_shape_ke.draw()
        if self._series_shape_pe:
            self._series_shape_pe.draw()
        if self._series_shape_total:
            self._series_shape_total.draw()

        # Draw legend
        self._draw_legend(plot_right, plot_top)

    def _draw_energy_line(
        self,
        time_data: list[float],
        energy_data: list[float],
        to_screen_coords,
        color: tuple[int, int, int],
        width: int,
    ):
        """Draw a single energy line on the plot."""
        for i in range(len(time_data) - 1):
            x1, y1 = to_screen_coords(time_data[i], energy_data[i])
            x2, y2 = to_screen_coords(time_data[i + 1], energy_data[i + 1])
            arcade.draw_line(x1, y1, x2, y2, color, width)

    def _draw_legend(self, plot_right: float, plot_top: float):
        """Draw the legend with current values."""
        legend_x = plot_right - 150
        legend_y = plot_top - 10

        if not self.kinetic_history:
            return

        # Get current values
        ke_current = self.kinetic_history[-1]
        pe_current = self.potential_history[-1]
        total_current = self.total_history[-1]

        # Update legend texts
        self.ke_legend_text.text = f"KE: {ke_current:.2f} J"
        self.ke_legend_text.x = legend_x
        self.ke_legend_text.y = legend_y

        self.pe_legend_text.text = f"PE: {pe_current:.2f} J"
        self.pe_legend_text.x = legend_x
        self.pe_legend_text.y = legend_y - 15

        self.total_legend_text.text = f"Total: {total_current:.2f} J"
        self.total_legend_text.x = legend_x
        self.total_legend_text.y = legend_y - 30

        # Draw legend background
        arcade.draw_lrbt_rectangle_filled(
            legend_x - 5,
            legend_x + 145,
            legend_y - 40,
            legend_y + 10,
            (255, 255, 255, 200),
        )

        # Draw legend texts
        self.ke_legend_text.draw()
        self.pe_legend_text.draw()
        self.total_legend_text.draw()

    def on_update(self, delta_time: float):
        """Update section."""
        pass


__all__: list[str] = ["EnergyManagerSection"]
