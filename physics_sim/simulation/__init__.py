__all__: list[str] = ["SimulationConfig", "Simulator"]

from physics_sim.simulation.config import SimulationConfig


def __getattr__(name: str):
    # Lazy: importing the simulator imports Kivy (which opens a window).
    if name == "Simulator":
        from physics_sim.simulation.simulator import Simulator

        return Simulator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
