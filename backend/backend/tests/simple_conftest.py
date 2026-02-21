"""
Simple test configuration without database dependencies
"""

import pytest
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock settings for testing
class MockSettings:
    ENCRYPTION_KEY = "test-encryption-key-32-chars!!"
    FIELD_ENCRYPTION_SALT = "test-salt-for-field-encryption"
    SECRET_KEY = "test-secret-key-32-chars-long!!"
    ENVIRONMENT = "testing"

# Mock the settings module
import sys
sys.modules['app.core.config'] = type('MockModule', (), {'settings': MockSettings()})()

@pytest.fixture
def mock_settings():
    return MockSettings()