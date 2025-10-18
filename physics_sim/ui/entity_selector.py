import numpy as np

from physics_sim.core import PhysicalEntity


class EntitySelector:
    """Handles entity selection via click detection and spatial queries."""

    def __init__(self):
        """Initialize selector with no selection."""
        self.selected_entity: PhysicalEntity | None = None
        self.selection_radius = 0.5  # Search radius for entity detection

    def select_entity(
        self, click_pos: np.ndarray, entities: list[PhysicalEntity]
    ) -> PhysicalEntity | None:
        """Find and select entity closest to click position.

        Args:
            click_pos: Click position in physics coordinates as np.ndarray([x, y])
            entities: List of entities to search

        Returns:
            Selected entity or None if no entity within selection radius
        """
        closest_entity = None
        min_distance = self.selection_radius

        for entity in entities:
            if not isinstance(entity, PhysicalEntity):
                continue

            # Calculate distance (handle both numpy arrays and Vector2D)
            if isinstance(entity.position, np.ndarray):
                distance = float(np.linalg.norm(entity.position - click_pos))
            else:
                distance = (entity.position - click_pos).magnitude()

            if distance < min_distance:
                min_distance = distance
                closest_entity = entity

        self.selected_entity = closest_entity
        return closest_entity

    def get_selected_entity(self) -> PhysicalEntity | None:
        """Get currently selected entity."""
        return self.selected_entity

    def clear_selection(self):
        """Clear current selection."""
        self.selected_entity = None

    def is_entity_selected(self) -> bool:
        """Check if any entity is currently selected."""
        return self.selected_entity is not None

    def set_selection_radius(self, radius: float):
        """Set the radius for entity detection.

        Args:
            radius: Detection radius in physics units
        """
        self.selection_radius = radius
