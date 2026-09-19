"""Compatibility package for standalone checkouts.

The application historically lives in a workspace folder named
``seedance_web``. Extending the package search path to the repository root
keeps imports such as ``from seedance_web import server`` working when this
repository is cloned under a different directory name.
"""

from pathlib import Path

__path__.append(str(Path(__file__).resolve().parent.parent))
