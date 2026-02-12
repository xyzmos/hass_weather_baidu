"""DataUpdateCoordinator for Baidu Weather integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    BaiduWeatherApiClient,
    BaiduWeatherApiError,
    BaiduWeatherAuthError,
    BaiduWeatherConnectionError,
)
from .const import (
    CONF_AK,
    CONF_DISTRICT_ID,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    KEY_ALERTS,
    KEY_FORECAST_HOURS,
    KEY_FORECASTS,
    KEY_INDEXES,
    KEY_LOCATION,
    KEY_NOW,
    MODE_DISTRICT,
)

_LOGGER = logging.getLogger(__name__)

type BaiduWeatherConfigEntry = ConfigEntry[BaiduWeatherCoordinator]


class BaiduWeatherCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for fetching Baidu Weather data."""

    config_entry: BaiduWeatherConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: BaiduWeatherConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.api = BaiduWeatherApiClient(
            session=async_get_clientsession(hass),
            ak=config_entry.data[CONF_AK],
        )
        self._mode = config_entry.data[CONF_MODE]
        self._district_id: str | None = config_entry.data.get(CONF_DISTRICT_ID)
        self._latitude: float | None = config_entry.data.get(CONF_LATITUDE)
        self._longitude: float | None = config_entry.data.get(CONF_LONGITUDE)

        update_interval = config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL.total_seconds()
        )
        from datetime import timedelta

        if isinstance(update_interval, (int, float)):
            update_interval = timedelta(seconds=update_interval)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=update_interval,
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Baidu Weather API."""
        try:
            if self._mode == MODE_DISTRICT and self._district_id:
                raw = await self.api.async_get_weather_by_district(
                    self._district_id
                )
            elif self._latitude is not None and self._longitude is not None:
                raw = await self.api.async_get_weather_by_location(
                    longitude=self._longitude,
                    latitude=self._latitude,
                )
            else:
                raise UpdateFailed("未配置有效的位置信息")
        except BaiduWeatherAuthError as err:
            raise UpdateFailed(f"API 认证失败: {err}") from err
        except BaiduWeatherConnectionError as err:
            raise UpdateFailed(f"连接失败: {err}") from err
        except BaiduWeatherApiError as err:
            raise UpdateFailed(f"API 错误: {err}") from err

        # Structure the returned data
        location_info = raw.get("location", {})
        now_data = raw.get("now", {})
        forecasts = raw.get("forecasts", [])
        forecast_hours = raw.get("forecast_hours", [])
        alerts = raw.get("alerts", [])
        indexes = raw.get("indexes", [])

        return {
            KEY_LOCATION: location_info,
            KEY_NOW: now_data,
            KEY_FORECASTS: forecasts,
            KEY_FORECAST_HOURS: forecast_hours,
            KEY_ALERTS: alerts,
            KEY_INDEXES: indexes,
        }
