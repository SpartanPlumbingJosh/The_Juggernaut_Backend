"""
Test configuration for the Autonomous & Self-Improvement system.
"""

import pytest
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test configuration
def pytest_configure(config):
    """
    Configure pytest for the Autonomous & Self-Improvement system.
    """
    # Register custom markers
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "performance: mark a test as a performance test")
    config.addinivalue_line("markers", "security: mark a test as a security test")
