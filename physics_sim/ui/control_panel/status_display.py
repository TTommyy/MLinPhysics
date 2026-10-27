from physics_sim.ui.utils import format_number
from physics_sim.ui.widgets import MUTED_TEXT_COLOR, TextLabel, vbox


class StatusDisplay:
    """Widget for displaying current application status and debug info."""

    def __init__(self):
        self.layout = vbox(spacing=2)
        self._current_fps = 0.0
        self._entity_counts: dict[str, int] = {}
        self._build()

    def _build(self):
        """Build widget layout."""
        self.layout.add_widget(TextLabel("Status", font_size=13, bold=True))
        self.fps_label = TextLabel("FPS: 0.00", font_size=12)
        self.layout.add_widget(self.fps_label)
        self.mode_label = TextLabel("Mode: Running", font_size=12)
        self.layout.add_widget(self.mode_label)
        self.counts_label = TextLabel(
            "No entities", font_size=12, color=MUTED_TEXT_COLOR
        )
        self.layout.add_widget(self.counts_label)
        # Kept for API compatibility (type name -> text)
        self.entity_count_labels: dict[str, str] = {}

    def update_debug_info(self, fps: float, entity_counts: dict[str, int]):
        """Update debug information.

        Args:
            fps: Current frames per second
            entity_counts: Dictionary mapping entity type names to counts
        """
        self._current_fps = fps
        fps_text = f"FPS: {format_number(fps)}"
        if self.fps_label.text != fps_text:
            self.fps_label.text = fps_text

        counts = dict(entity_counts or {})
        if counts == self._entity_counts and self.entity_count_labels:
            return
        self._entity_counts = counts
        if counts:
            self.entity_count_labels = {
                name: f"{name}: {count}" for name, count in counts.items()
            }
            self.counts_label.text = "\n".join(self.entity_count_labels.values())
        else:
            self.entity_count_labels = {"no_entities": "No entities"}
            self.counts_label.text = "No entities"

    def set_mode(self, add_mode: bool, paused: bool):
        """Display current interaction mode."""
        if add_mode:
            text = "Mode: Add (click viewport to place)"
        elif paused:
            text = "Mode: Edit (click entity to select)"
        else:
            text = "Mode: Running"
        if self.mode_label.text != text:
            self.mode_label.text = text

    def get_layout(self):
        """Get the widget layout."""
        return self.layout


__all__: list[str] = ["StatusDisplay"]
