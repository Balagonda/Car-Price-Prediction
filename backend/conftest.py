"""
AutoWorth AI — Pytest Configuration

Configure async test environment.
"""

import pytest
import pytest_asyncio


# Use asyncio event loop for all async tests
pytest_plugins = ["pytest_asyncio"]
