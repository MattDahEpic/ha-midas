"""Fixtures for testing."""

import pytest

pytest_plugins = ["aiohttp.pytest_plugin"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable actually testing with the custom integration."""
    yield
