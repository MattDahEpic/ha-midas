"""Fixtures for testing."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.midas.const import (
    CONF_PASSWORD,
    CONF_RATEIDS,
    CONF_USERNAME,
    DOMAIN,
)

pytest_plugins = ["aiohttp.pytest_plugin"]  # makes AiohttpClientMocker work


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable actually testing with the custom integration."""
    yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.midas.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the mocked config entry."""
    return MockConfigEntry(
        title="MIDAS Account: test",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
            CONF_RATEIDS: ["TEST-TEST-TEST-TEST"],
        },
    )
