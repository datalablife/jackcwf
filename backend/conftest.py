"""
Pytest configuration and fixtures for backend tests.

Sets up Python path and test fixtures.
"""

import sys
import os
from pathlib import Path

# Add backend src directory to Python path
backend_src = Path(__file__).parent / "src"
sys.path.insert(0, str(backend_src.parent))

# Load .env for tests
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
