import arcade.gui


class EngineControls:
    """Widget group for physics engine selection."""

    def __init__(self, initial_engine: str = "numpy"):
        self.selected_engine = initial_engine
        self.on_engine_change = None

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

        # Engine toggle button
        self.engine_button = arcade.gui.UIFlatButton(
            text=self.selected_engine.upper(),
            width=220,
            height=35,
        )
        self.engine_button.on_click = self._toggle_engine
        self.layout.add(self.engine_button)

    def _toggle_engine(self, event):
        """Toggle between numpy and pymunk engines."""
        self.selected_engine = "pymunk" if self.selected_engine == "numpy" else "numpy"
        self.engine_button.text = self.selected_engine.upper()
        if self.on_engine_change:
            self.on_engine_change(self.selected_engine)

    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["EngineControls"]
