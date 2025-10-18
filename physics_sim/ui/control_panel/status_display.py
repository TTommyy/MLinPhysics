import arcade.gui


class StatusDisplay:
    """Widget for displaying current application status and debug info."""

    def __init__(self):
        self.layout = arcade.gui.UIBoxLayout(space_between=8, vertical=True)
        self._current_fps = 0.0
        self._entity_counts = {}
        self._build()

    def _build(self):
        """Build widget layout."""
        # Debug info labels
        self.fps_label = arcade.gui.UILabel(
            text="FPS: 0",
            font_size=9,
            text_color=arcade.color.BLACK_LEATHER_JACKET,
        )
        self.layout.add(self.fps_label)

        # Entity counts - will be dynamically created
        self.entity_count_labels = {}


    def update_debug_info(self, fps: float, entity_counts: dict[str, int]):
        """Update debug information.

        Args:
            fps: Current frames per second
            entity_counts: Dictionary mapping entity type names to counts
        """
        self.fps_label.text = f"FPS: {fps:.0f}"

        # Remove old entity count labels that no longer exist
        for type_name in list(self.entity_count_labels.keys()):
            if type_name != "no_entities" and type_name not in entity_counts:
                label = self.entity_count_labels.pop(type_name)
                self.layout.remove(label)

        # Update or create labels for each entity type
        if entity_counts:
            # Remove "no_entities" placeholder if it exists
            if "no_entities" in self.entity_count_labels:
                label = self.entity_count_labels.pop("no_entities")
                self.layout.remove(label)

            for type_name, count in entity_counts.items():
                if type_name not in self.entity_count_labels:
                    # Create new label
                    label = arcade.gui.UILabel(
                        text=f"{type_name}: {count}",
                        font_size=9,
                        text_color=arcade.color.BLACK_LEATHER_JACKET,
                    )
                    self.entity_count_labels[type_name] = label
                    self.layout.add(label)
                else:
                    # Update existing label
                    self.entity_count_labels[type_name].text = f"{type_name}: {count}"
        else:
            # Show "No entities" if nothing exists
            if "no_entities" not in self.entity_count_labels:
                label = arcade.gui.UILabel(
                    text="No entities",
                    font_size=9,
                    text_color=arcade.color.DARK_GRAY,
                )
                self.entity_count_labels["no_entities"] = label
                self.layout.add(label)

    def get_layout(self) -> arcade.gui.UIBoxLayout:
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["StatusDisplay"]
