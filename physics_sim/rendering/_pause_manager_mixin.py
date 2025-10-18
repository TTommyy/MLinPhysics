class PauseManagerMixin:
    """Mixin for managing pause state of the simulation."""

    def pause(self) -> None:
        """Pauses the simulation."""
        self._paused = True

    def is_paused(self) -> bool:
        """Returns True if the simulation is paused."""
        return self._paused

    def toggle_pause(self) -> None:
        """Toggles the pause state of the simulation."""
        self._paused = not self._paused
