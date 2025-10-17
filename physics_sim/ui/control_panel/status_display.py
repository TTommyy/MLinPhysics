import arcade.gui


class StatusDisplay:
    """Widget for displaying current application status."""

    def __init__(self):
        self.layout = arcade.gui.UIBoxLayout(space_between=8, vertical=True)
        self._build()

    def _build(self):
        """Build widget layout."""
        self.status_label = arcade.gui.UILabel(
            text="● Normal",
            font_size=11,
            text_color=arcade.color.DARK_GREEN,
        )
        self.layout.add(self.status_label)

    def set_status(
        self, text: str, color: tuple[int, int, int] = arcade.color.DARK_GREEN
    ):
        """Update status text and color."""
        self.status_label.text = text
        self.status_label.text_color = color

    def set_normal(self):
        """Set status to normal."""
        self.set_status("● Normal", arcade.color.DARK_GREEN)

    def set_adding(self, entity_name: str):
        """Set status to adding mode."""
        self.set_status(f"● Adding {entity_name}", arcade.color.ORANGE)

    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["StatusDisplay"]
