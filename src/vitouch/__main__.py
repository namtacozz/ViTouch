"""Entry point for running ViTouch."""

import sys
from pathlib import Path

# Ensure src/ is in sys.path when running directly
src_dir = str(Path(__file__).parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from vitouch.app import ViTouchApp


def main():
    app = ViTouchApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
