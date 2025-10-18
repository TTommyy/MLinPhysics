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
    gravity: Vector2D = Vector2D(0.0, 10.0)
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
        """Create config maintaining aspect ratio from screen dimensions."""
        sim_min_width = 10.0
        aspect_ratio = width / height
        sim_width = sim_min_width
        sim_height = sim_min_width / aspect_ratio

        return cls(
            screen_width=width,
            screen_height=height,
            sim_width=sim_width,
            sim_height=sim_height,
        )
