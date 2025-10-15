"""Main entry point for physics simulation.

Provides a command-line interface for running different demos
and selecting physics engines.

Usage:
    python main.py                    # Run basic cannonball demo
    python main.py --engine pymunk    # Use pymunk engine
    python main.py --demo compare     # Run comparison demo
    python main.py --demo many        # Run many balls demo
"""

import argparse

import arcade

from physics_sim import (
    Ball,
    DragForce,
    GravityForce,
    NumpyPhysicsEngine,
    PymunkPhysicsEngine,
    SimulationConfig,
    Simulator,
)


def create_basic_demo(config: SimulationConfig):
    """Create basic cannonball demo."""
    if config.engine_type == "numpy":
        engine = NumpyPhysicsEngine(
            gravity=config.gravity,
            bounds=(config.sim_width, config.sim_height),
        )
        # Add forces to numpy engine
        engine.add_force(GravityForce(config.gravity))
        engine.add_force(DragForce())
    else:
        engine = PymunkPhysicsEngine(
            gravity=config.gravity,
            bounds=(config.sim_width, config.sim_height),
        )

    ball = Ball.create_cannonball()
    engine.add_entity(ball)

    return engine


def create_multi_ball_demo(config: SimulationConfig, count: int = 10):
    """Create demo with multiple random balls."""
    if config.engine_type == "numpy":
        engine = NumpyPhysicsEngine(
            gravity=config.gravity,
            bounds=(config.sim_width, config.sim_height),
        )
        # Add forces to numpy engine
        engine.add_force(GravityForce(config.gravity))
        engine.add_force(DragForce())
    else:
        engine = PymunkPhysicsEngine(
            gravity=config.gravity,
            bounds=(config.sim_width, config.sim_height),
        )
        engine.add_force(DragForce())

    for _ in range(count):
        ball = Ball.create_random((config.sim_width, config.sim_height))
        engine.add_entity(ball)

    return engine


def main():
    parser = argparse.ArgumentParser(
        description="Physics Simulation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Basic cannonball demo
  python main.py --engine pymunk           # Use Pymunk engine
  python main.py --demo many --count 50    # 50 random balls
        """,
    )

    parser.add_argument(
        "--engine",
        choices=["numpy", "pymunk"],
        default="pymunk",
        help="Physics engine to use (default: numpy)",
    )

    parser.add_argument(
        "--demo",
        choices=["basic", "many", "compare"],
        default="basic",
        help="Demo to run (default: basic)",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of balls for 'many' demo (default: 10)",
    )

    args = parser.parse_args()

    # Create configuration
    config = SimulationConfig.from_screen_size(
        arcade.get_display_size()[0], arcade.get_display_size()[1]
    )
    config.engine_type = args.engine

    # Create appropriate demo
    if args.demo == "basic":
        config.window_title = f"Cannonball Demo - {args.engine.capitalize()}"
        engine = create_basic_demo(config)
    elif args.demo == "many":
        config.window_title = f"Many Balls - {args.count} balls ({args.engine})"
        engine = create_multi_ball_demo(config, args.count)
    else:  # compare
        print("For comparison demo, run: python examples/compare_engines.py")
        return

    # Print info
    print("Physics Simulation Framework")
    print("===========================")
    print(f"Engine: {args.engine}")
    print(f"Demo: {args.demo}")
    print(f"Window: {arcade.get_display_size()[0]}x{arcade.get_display_size()[1]}")
    print()
    print("Controls:")
    print("  F1  - Toggle debug info")
    print("  G   - Toggle grid")
    print("  A   - Toggle add mode (click to add objects)")
    print("  TAB - Cycle object type (in add mode)")
    print("  ESC - Exit add mode / Exit simulation")
    print()
    print("UI Buttons:")
    print("  Grid/Debug buttons - Toggle display options")
    print()
    print("UI Layout:")
    print("  Left Panel   - Controls and shortcuts")
    print("  Center       - Simulation viewport")
    print("  Right Panel  - Entity inventory")
    print()

    # Run simulation
    simulator = Simulator(config, engine)
    simulator.run()


if __name__ == "__main__":
    main()
