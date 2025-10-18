import arcade.gui


class EngineControls:
    """Widget group for physics engine selection."""

    def __init__(self, initial_engine: str = "numpy", button_width: int = 220):
        self.selected_engine = initial_engine
        self.on_engine_change = None
        self.button_width = button_width

        self.layout = arcade.gui.UIBoxLayout(space_between=8, vertical=True)
        self._build()

    def _build(self):
        """Build widget layout."""
        # Section label
        label = arcade.gui.UILabel(
            text="Physics Engine",
            font_size=10,
            text_color=arcade.color.DARK_GRAY,
        )
        self.layout.add(label)


    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["EngineControls"]
