"""Test the MIDAS data update coordinator."""

# ignore errors that shouldn't matter in this test file
# ruff: noqa: S101

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from california_midasapi.exception import (
    MidasAuthenticationException,
    MidasCommunicationException,
    MidasException,
    MidasNotFoundException,
)
from california_midasapi.types import RateInfo, ValueInfoItem
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.midas.api import IntegrationMidasApiClient
from custom_components.midas.const import CONF_RATEIDS, DOMAIN
from custom_components.midas.coordinator import MidasDataUpdateCoordinator
from custom_components.midas.data import IntegrationMidasData

STALE_RATE_ID = "USCA-TEST-STAL-0000"
HEALTHY_RATE_ID = "USCA-TEST-GOOD-0000"


def _rate_info(rate_id: str, *, with_tariff: bool) -> RateInfo:
    """Build a RateInfo, optionally holding one currently active tariff."""
    tariffs = []
    if with_tariff:
        # Span yesterday to tomorrow so the tariff is active whenever this runs.
        # The two day spread also avoids GetEnd()'s next-day correction, which
        # needs both an exactly-one-day range and DayStart == DayEnd.
        today = datetime.now()  # noqa: DTZ005
        tariffs.append(
            ValueInfoItem(
                ValueName="Test",
                DateStart=(today - timedelta(days=1)).strftime("%Y-%m-%d"),
                DateEnd=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
                DayStart="1",
                DayEnd="3",
                TimeStart="00:00:00",
                TimeEnd="23:59:59",
                Value=0.12345,
                Unit="$/kWh",
            )
        )
    return RateInfo(
        RateID=rate_id,
        SystemTime_UTC="",
        RateName="Test Rate",
        RateType="TOU",
        Sector="Res",
        API_Url="",
        RatePlan_Url="",
        EndUse="All",
        AltRateName1="",
        AltRateName2="",
        SignalType="Electricity Rates",
        Description="",
        SignupCloseDate="",
        ValueInformation=tariffs,
    )


async def _setup_with(
    hass: HomeAssistant, rate_ids: list[str], historical_error: Exception
) -> MockConfigEntry:
    """Set up the integration where the historical lookup raises."""
    entry = MockConfigEntry(
        title="MIDAS",
        domain=DOMAIN,
        data={CONF_RATEIDS: rate_ids},
    )
    entry.add_to_hass(hass)

    async def _get_rate_data(_self, rate_id: str) -> RateInfo:
        # The stale rate id still answers, it just has no active tariffs.
        return _rate_info(rate_id, with_tariff=rate_id != STALE_RATE_ID)

    async def _get_historical_rate_data(_self, rate_id: str) -> RateInfo:
        raise historical_error

    with (
        patch.object(IntegrationMidasApiClient, "async_get_rate_data", _get_rate_data),
        patch.object(
            IntegrationMidasApiClient,
            "async_get_historical_rate_data",
            _get_historical_rate_data,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


async def test_coordinator_stale_rate_id_does_not_break_the_others(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    """A rate id with no data must not take down the rest of the integration.

    A rate id whose data has gone stale answers the historical endpoint with a
    404 rather than an empty result. That used to escape the loop over every
    configured rate id, so one stale utility made every sensor unavailable,
    including sensors for rate ids that were perfectly healthy.
    """
    entry = await _setup_with(
        hass,
        [STALE_RATE_ID, HEALTHY_RATE_ID],
        MidasNotFoundException("Requested data not found: 404"),
    )

    assert entry.state is ConfigEntryState.LOADED

    coordinator = entry.runtime_data.coordinator
    assert coordinator.last_update_success
    # sensor.py indexes coordinator.data[rate_id] unguarded, so the stale key
    # must survive rather than be dropped.
    assert STALE_RATE_ID in coordinator.data
    # And the healthy rate id was still fetched, despite being ordered after
    # the stale one.
    assert HEALTHY_RATE_ID in coordinator.data
    assert len(coordinator.data[HEALTHY_RATE_ID].GetCurrentTariffs()) == 1

    # And the stale one reports itself through the repair it already has.
    assert issue_registry.async_get_issue(DOMAIN, f"no_tarrifs_{STALE_RATE_ID.lower()}")
    assert not issue_registry.async_get_issue(
        DOMAIN, f"no_tarrifs_{HEALTHY_RATE_ID.lower()}"
    )


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (MidasAuthenticationException("Invalid credentials"), ConfigEntryAuthFailed),
        (MidasCommunicationException("Connection reset"), UpdateFailed),
        (MidasException("Error preforming request: 500"), UpdateFailed),
    ],
)
async def test_coordinator_real_failures_are_not_swallowed(
    hass: HomeAssistant,
    error: Exception,
    expected: type[Exception],
) -> None:
    """A real failure must still fail the update, not look like "no tariffs".

    Only a 404 means "this rate id has no data". Anything else, including a
    plain MidasException from a 500, has to reach the coordinator's own
    handler so the update fails, rather than being reported as a successful
    update plus a repair telling the user to contact their utility about a
    rate id that is actually fine.

    This drives the coordinator directly rather than going through setup,
    because ConfigEntryAuthFailed makes Home Assistant start a reauth flow and
    MidasFlowHandler has no reauth step to start.
    """
    entry = MockConfigEntry(
        title="MIDAS",
        domain=DOMAIN,
        data={CONF_RATEIDS: [STALE_RATE_ID]},
    )
    entry.add_to_hass(hass)

    coordinator = MidasDataUpdateCoordinator(
        hass=hass, client=IntegrationMidasApiClient(hass=hass)
    )
    coordinator.config_entry = entry
    entry.runtime_data = IntegrationMidasData(
        coordinator=coordinator, rate_ids=[STALE_RATE_ID]
    )

    async def _get_rate_data(_self, rate_id: str) -> RateInfo:
        return _rate_info(rate_id, with_tariff=False)

    async def _get_historical_rate_data(_self, rate_id: str) -> RateInfo:
        raise error

    with (
        patch.object(IntegrationMidasApiClient, "async_get_rate_data", _get_rate_data),
        patch.object(
            IntegrationMidasApiClient,
            "async_get_historical_rate_data",
            _get_historical_rate_data,
        ),
        pytest.raises(expected),
    ):
        await coordinator._async_update_data()  # noqa: SLF001


async def test_coordinator_unknown_rate_id_still_fails_the_update(
    hass: HomeAssistant,
) -> None:
    """A rate id that does not exist must fail loudly, not look like "no tariffs".

    The API answers 404 for both "this rate id has no data in that window" and
    "this rate id does not exist", so the two are only told apart by which call
    raised. A nonexistent rate id 404s on the primary lookup, which is outside
    the handler, and has to stay an UpdateFailed rather than becoming a repair
    that blames the user's utility.
    """
    entry = MockConfigEntry(
        title="MIDAS",
        domain=DOMAIN,
        data={CONF_RATEIDS: [STALE_RATE_ID]},
    )
    entry.add_to_hass(hass)

    coordinator = MidasDataUpdateCoordinator(
        hass=hass, client=IntegrationMidasApiClient(hass=hass)
    )
    coordinator.config_entry = entry
    entry.runtime_data = IntegrationMidasData(
        coordinator=coordinator, rate_ids=[STALE_RATE_ID]
    )

    async def _get_rate_data(_self, rate_id: str) -> RateInfo:
        raise MidasNotFoundException(f"RIN not found: {rate_id}")

    with (
        patch.object(IntegrationMidasApiClient, "async_get_rate_data", _get_rate_data),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()  # noqa: SLF001
