import logging

import arcade

from physics_sim import (
    Ball,
    DragForce,
    GravityForce,
    NumpyPhysicsEngine,
    SimulationConfig,
    Simulator,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    # Create configuration
    config = SimulationConfig.from_screen_size(
        arcade.get_display_size()[0], arcade.get_display_size()[1]
    )

    # Print info
    engine = NumpyPhysicsEngine(
        gravity=config.gravity,
        bounds=(config.sim_width, config.sim_height),
    )
    # Add forces to numpy engine
    engine.add_force(GravityForce(config.gravity))
    engine.add_force(DragForce())
    ball = Ball.create_cannonball()
    engine.add_entity(ball)
    # Run simulation
    simulator = Simulator(config, engine)
    simulator.run()


if __name__ == "__main__":
    main()
