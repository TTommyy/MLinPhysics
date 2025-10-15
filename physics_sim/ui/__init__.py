__all__: list[str] = ["InventoryPanel", "ControlPanel"]

try:
    from physics_sim.ui.control_panel import ControlPanel
    from physics_sim.ui.inventory_panel import InventoryPanel
except ImportError:
    # Arcade not installed, create stub classes
    class ControlPanel:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Arcade is not installed. Install with: pip install arcade"
            )

    class InventoryPanel:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Arcade is not installed. Install with: pip install arcade"
            )
