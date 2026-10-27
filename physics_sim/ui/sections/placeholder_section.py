from physics_sim.core import LayoutRegion
from physics_sim.ui.sections.base_section import BaseSection
from physics_sim.ui.widgets import TextLabel


class PlaceholderSection(BaseSection):
    """Placeholder section for future UI components."""

    def __init__(
        self,
        region: LayoutRegion | None,
        label: str,
        background_color: tuple[int, int, int] = (220, 220, 240),
    ):
        super().__init__(region, background_color=background_color)
        self.label = TextLabel(
            label, font_size=18, bold=True, color=(110, 110, 110), halign="center",
            size_hint_y=1,
        )
        self.add_widget(self.label)


__all__: list[str] = ["PlaceholderSection"]
