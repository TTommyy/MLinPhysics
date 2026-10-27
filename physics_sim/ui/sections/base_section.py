from physics_sim.core import LayoutRegion
from physics_sim.ui.widgets import Panel


class BaseSection(Panel):
    """Base section: a Kivy panel (BoxLayout) with background and border.

    Sections are laid out by their parent layout; ``region`` reflects the
    current on-screen rectangle of the section.
    """

    def __init__(
        self,
        region: LayoutRegion | None = None,
        background_color: tuple[int, int, int] = (245, 245, 245),
        border_color: tuple[int, int, int] | None = (160, 160, 160),
        border_width: float = 1.0,
        **kwargs,
    ):
        kwargs.setdefault("orientation", "vertical")
        super().__init__(
            background_color=background_color,
            border_color=border_color,
            border_width=border_width,
            **kwargs,
        )
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
        self._initial_region = region
        if region is not None and region.width > 0 and region.height > 0:
            self.pos = (region.x, region.y)
            self.size = (region.width, region.height)

    @property
    def region(self) -> LayoutRegion:
        """Current on-screen region of the section."""
        return LayoutRegion(
            int(self.x), int(self.y), int(self.width), int(self.height)
        )

    def enable(self):
        """Enable user interaction."""
        self.disabled = False

    def disable(self):
        """Disable user interaction."""
        self.disabled = True

    def on_update(self, delta_time: float):
        """Per-frame update hook."""
        pass


__all__: list[str] = ["BaseSection"]
