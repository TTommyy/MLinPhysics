from physics_sim.core import LayoutRegion


class LayoutManager:
    """Manages UI layout using percentage-based positioning.

    Calculates screen regions for all UI components based on
    screen dimensions and percentage configurations.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        control_panel_width_pct: float = 0.20,
        inventory_panel_width_pct: float = 0.25,
        viewport_height_pct: float = 0.50,
    ):
        """
        Args:
            screen_width: Total screen width in pixels
            screen_height: Total screen height in pixels
            control_panel_width_pct: Control panel width as percentage (0.0-1.0)
            inventory_panel_width_pct: Inventory panel width as percentage (0.0-1.0)
            viewport_height_pct: Viewport height as percentage (0.0-1.0)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Calculate pixel dimensions from percentages
        control_width = int(screen_width * control_panel_width_pct)
        inventory_width = int(screen_width * inventory_panel_width_pct)
        middle_width = screen_width - control_width - inventory_width

        viewport_height = int(screen_height * viewport_height_pct)
        top_height = int(screen_height * (1.0 - viewport_height_pct) / 2)
        bottom_height = screen_height - viewport_height - top_height

        # Define regions
        self._control_panel = LayoutRegion(
            x=0, y=0, width=control_width, height=screen_height
        )

        self._inventory_panel = LayoutRegion(
            x=control_width + middle_width,
            y=0,
            width=inventory_width,
            height=screen_height,
        )

        self._top_placeholder = LayoutRegion(
            x=control_width,
            y=viewport_height + bottom_height,
            width=middle_width,
            height=top_height,
        )

        self._viewport = LayoutRegion(
            x=control_width, y=bottom_height, width=middle_width, height=viewport_height
        )

        self._bottom_placeholder = LayoutRegion(
            x=control_width, y=0, width=middle_width, height=bottom_height
        )

    @property
    def control_panel(self) -> LayoutRegion:
        """Left control panel region (full height)."""
        return self._control_panel

    @property
    def inventory_panel(self) -> LayoutRegion:
        """Right inventory panel region (full height)."""
        return self._inventory_panel

    @property
    def viewport(self) -> LayoutRegion:
        """Middle simulation viewport region."""
        return self._viewport

    @property
    def top_placeholder(self) -> LayoutRegion:
        """Top placeholder region in middle column."""
        return self._top_placeholder

    @property
    def bottom_placeholder(self) -> LayoutRegion:
        """Bottom placeholder region in middle column."""
        return self._bottom_placeholder


__all__: list[str] = ["LayoutManager", "LayoutRegion"]
