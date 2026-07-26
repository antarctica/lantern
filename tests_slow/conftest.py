"""Imports all fixtures from main test suite."""

import sys
from pathlib import Path

# Include tests/ to Python search path
tests_dir = Path(__file__).parent.parent / "tests"
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

from conftest import *  # noqa: E402, F403
