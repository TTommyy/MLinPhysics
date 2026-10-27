###
# uv run watchfiles "uv run main.py" physics_sim main.py
###

import logging

from physics_sim import (
    NumpyPhysicsEngine,
    SimulationConfig,
    Simulator,
)
from physics_sim.ui.utils import get_display_size

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    # Create configuration
    config = SimulationConfig.from_screen_size(*get_display_size())

    # Create engine
    engine = NumpyPhysicsEngine(
        bounds=(config.sim_width, config.sim_height),
    )
    # Add forces to numpy engine
    # engine.add_force(LinearGravityForce())
    # engine.add_force(DragForce())
    # ball = Ball.create_cannonball()
    # engine.add_entity(ball)
    # Run simulation
    simulator = Simulator(config, engine)
    simulator.run()


if __name__ == "__main__":
    main()
