"""
pytest configuration for Valley Teacher Coverage App
"""

import pytest
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import fixtures
from tests.fixtures import *
