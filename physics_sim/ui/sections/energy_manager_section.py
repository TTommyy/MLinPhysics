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

        # Draw plot border
        arcade.draw_lrbt_rectangle_outline(
            plot_left,
            plot_right,
            plot_bottom,
            plot_top,
            arcade.color.GRAY,
            2,
        )

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

        # Draw grid lines (horizontal)
        num_h_lines = 5
        for i in range(num_h_lines + 1):
            y = plot_bottom + (plot_height * i / num_h_lines)
            arcade.draw_line(
                plot_left,
                y,
                plot_right,
                y,
                (200, 200, 200),
                1,
            )
            # Y-axis labels
            energy_value = energy_min + (energy_range * i / num_h_lines)
            label = arcade.Text(
                f"{energy_value:.1f}",
                plot_left - 5,
                y - 5,
                arcade.color.BLACK,
                8,
                anchor_x="right",
            )
            label.draw()

        # Draw grid lines (vertical)
        num_v_lines = 6
        for i in range(num_v_lines + 1):
            x = plot_left + (plot_width * i / num_v_lines)
            arcade.draw_line(
                x,
                plot_bottom,
                x,
                plot_top,
                (200, 200, 200),
                1,
            )
            # X-axis labels
            if i % 2 == 0:  # Only show every other label
                time_value = time_min + (time_range * i / num_v_lines)
                label = arcade.Text(
                    f"{time_value:.1f}",
                    x,
                    plot_bottom - 15,
                    arcade.color.BLACK,
                    8,
                    anchor_x="center",
                )
                label.draw()

        # Helper function to convert data to screen coordinates
        def to_screen_coords(time_val: float, energy_val: float) -> tuple[float, float]:
            x = plot_left + ((time_val - time_min) / time_range) * plot_width
            y = plot_bottom + ((energy_val - energy_min) / energy_range) * plot_height
            return x, y

        # Draw energy lines
        self._draw_energy_line(
            self.time_history,
            self.kinetic_history,
            to_screen_coords,
            arcade.uicolor.BLUE_PETER_RIVER,
            2,
        )
        self._draw_energy_line(
            self.time_history,
            self.potential_history,
            to_screen_coords,
            arcade.uicolor.RED_POMEGRANATE,
            2,
        )
        self._draw_energy_line(
            self.time_history,
            self.total_history,
            to_screen_coords,
            arcade.uicolor.GREEN_NEPHRITIS,
            3,
        )

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
