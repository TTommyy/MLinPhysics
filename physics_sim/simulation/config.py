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

    # Panel dimensions
    control_panel_width: int = 250
    inventory_panel_width: int = 350

    # Physics settings
    sim_width: float = 20.0
    sim_height: float = 13.33
    gravity: Vector2D = Vector2D(0.0, 10.0)
    timestep: float = 1.0 / 60.0

    # Engine selection
    engine_type: str = "numpy"  # "numpy" or "pymunk"

    # Debug settings
    show_debug_info: bool = True

    @property
    def viewport_x(self) -> int:
        """X coordinate where viewport starts (after left panel)."""
        return self.control_panel_width

    @property
    def viewport_width(self) -> int:
        """Width of the simulation viewport."""
        return self.screen_width - self.control_panel_width - self.inventory_panel_width

    @property
    def viewport_height(self) -> int:
        """Height of the simulation viewport."""
        return self.screen_height

    @classmethod
    def from_screen_size(cls, width: int, height: int) -> "SimulationConfig":
        """Create config maintaining aspect ratio from screen dimensions."""
        sim_min_width = 20.0
        aspect_ratio = width / height
        sim_width = sim_min_width
        sim_height = sim_min_width / aspect_ratio

        return cls(
            screen_width=width,
            screen_height=height,
            sim_width=sim_width,
            sim_height=sim_height,
        )

    @classmethod
    def cannonball_demo(cls) -> "SimulationConfig":
        """Config matching the original JavaScript cannonball demo."""
        return cls(
            screen_width=1200,
            screen_height=800,
            window_title="Cannonball Demo",
            engine_type="numpy",
        )

    @classmethod
    def pymunk_demo(cls) -> "SimulationConfig":
        """Config for demonstrating Pymunk engine."""
        return cls(
            screen_width=1200,
            screen_height=800,
            window_title="Pymunk Physics Demo",
            engine_type="pymunk",
        )
