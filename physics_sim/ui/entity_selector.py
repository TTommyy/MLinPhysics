import numpy as np


class EntitySelector:
    """Handles entity selection via click detection and spatial queries."""

    def __init__(self):
        """Initialize selector with no selection."""
        self.selected_entity_id: str | None = None
        self.selection_radius = 1  # Search radius for entity detection

    def select_entity(
        self, click_pos: np.ndarray, render_data: list[dict]
    ) -> str | None:
        """Find and select entity ID closest to click position.

        Args:
            click_pos: Click position in physics coordinates as np.ndarray([x, y])
            render_data: List of render data dicts from engine

        Returns:
            Selected entity ID or None if no entity within selection radius
        """
        closest_id = None
        min_distance = self.selection_radius

        for data in render_data:
            pos = np.array(data["position"])
            distance = float(np.linalg.norm(pos - click_pos))

            if distance < min_distance:
                min_distance = distance
                closest_id = data["id"]

        self.selected_entity_id = closest_id
        return closest_id

    def get_selected_entity(self):
        """Get currently selected entity ID.

        Note: Returns ID, not entity object. Use engine.get_entity_for_editing(id)
        to get the entity object for editing.
        """
        return self.selected_entity_id

    def clear_selection(self):
        """Clear current selection."""
        self.selected_entity_id = None

    def is_entity_selected(self) -> bool:
        """Check if any entity is currently selected."""
        return self.selected_entity_id is not None

    def set_selection_radius(self, radius: float):
        """Set the radius for entity detection.

        Args:
            radius: Detection radius in physics units
        """
        self.selection_radius = radius
