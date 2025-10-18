from dataclasses import dataclass

from physics_sim.core import Vector2D


@dataclass
class SimulationConfig:
    """Configuration for physics simulation.

    Centralizes all simulation parameters for easy modification
    and experimentation.
    """

    # Display settings
    screen_width: int = 1200
    screen_height: int = 800
    window_title: str = "Physics Simulation"

    # Layout percentages
    control_panel_width_pct: float = 0.20
    inventory_panel_width_pct: float = 0.20
    viewport_height_pct: float = 0.50

    # Physics settings
    sim_width: float = 12
    sim_height: float = 8
    gravity: Vector2D = Vector2D(0.0, -9.81)
    timestep: float = 1.0 / 60.0

    # Engine selection
    engine_type: str = "numpy"  # "numpy" or "pymunk"

    # Debug settings
    show_debug_info: bool = True

    def create_layout_manager(self):
        """Create a LayoutManager instance from this config.

        Returns:
            LayoutManager configured with screen dimensions and percentages
        """
        from physics_sim.ui.layout import LayoutManager

        return LayoutManager(
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            control_panel_width_pct=self.control_panel_width_pct,
            inventory_panel_width_pct=self.inventory_panel_width_pct,
            viewport_height_pct=self.viewport_height_pct,
        )

    @classmethod
    def from_screen_size(cls, width: int, height: int) -> "SimulationConfig":
        """Create config maintaining aspect ratio from screen dimensions.

        This method calculates the simulation dimensions based on the actual
        viewport region size (after accounting for control panels), not the
        full screen size.
        """
        # Use default layout percentages
        control_panel_width_pct = 0.15
        inventory_panel_width_pct = 0.15
        viewport_height_pct = 0.60

        # Calculate actual viewport dimensions
        control_width = int(width * control_panel_width_pct)
        inventory_width = int(width * inventory_panel_width_pct)
        viewport_width = width - control_width - inventory_width
        viewport_height = int(height * viewport_height_pct)

        # Calculate simulation dimensions based on viewport aspect ratio
        sim_min_width = 100.0
        viewport_aspect_ratio = viewport_width / viewport_height
        sim_width = sim_min_width
        sim_height = sim_min_width / viewport_aspect_ratio

        return cls(
            screen_width=width,
            screen_height=height,
            sim_width=sim_width,
            sim_height=sim_height,
            control_panel_width_pct=control_panel_width_pct,
            inventory_panel_width_pct=inventory_panel_width_pct,
            viewport_height_pct=viewport_height_pct,
        )
