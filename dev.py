#!/usr/bin/env python3
"""Hot-reload development runner for Arcade simulation.

Watches physics_sim modules for changes and automatically restarts the window.
"""

import json
import logging
import os
from pathlib import Path

from watchfiles import run_process

logger = logging.getLogger("DevReloader")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logging.getLogger("watchfiles").setLevel(logging.WARNING)


def on_changes(changes):
    """Callback when files change."""
    logger.info(f"🔄 Files changed: {len(changes)} file(s)")
    for change_type, file_path in changes:
        logger.debug(f"  {change_type}: {file_path}")


def run_simulation():
    """Run the simulation (called in subprocess by run_process)."""
    changes = os.getenv("WATCHFILES_CHANGES", "[]")
    changes = json.loads(changes)

    if changes:
        logger.info(f"▶️  Restarting due to {len(changes)} change(s)")
    else:
        logger.info("▶️  Starting simulation...")

    from main import main

    main()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Dev Mode: Auto-restart on file changes")
    print("📁 Watching: physics_sim/")
    print("⌨️  Press Ctrl+C to exit")
    print("=" * 60)

    watch_path = Path.cwd() / "physics_sim"

    try:
        reload_count = run_process(
            str(watch_path),
            target=run_simulation,
            callback=on_changes,
            debounce=1600,
            grace_period=0.5,
        )
        logger.info(f"✓ Exited cleanly after {reload_count} reload(s)")
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down dev mode")
