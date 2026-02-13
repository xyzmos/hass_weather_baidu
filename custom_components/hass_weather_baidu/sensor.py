"""Sensor entities for Baidu Weather integration - Weather Alerts & Forecasts."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_LOCATION_NAME,
    DOMAIN,
    KEY_ALERTS,
    KEY_FORECASTS,
    KEY_NOW,
)
from .coordinator import BaiduWeatherCoordinator

_LOGGER = logging.getLogger(__name__)

# Day labels for forecast sensors (index 0 = today)
_DAY_LABELS_CN = ["今天", "明天", "后天", "大后天", "第五天"]
_DAY_LABELS_EN = ["Today", "Tomorrow", "Day After Tomorrow", "In 3 Days", "In 4 Days"]
_DAY_KEYS = ["forecast_today", "forecast_tomorrow", "forecast_day2", "forecast_day3", "forecast_day4"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Baidu Weather sensor entities from a config entry."""
    coordinator: BaiduWeatherCoordinator = entry.runtime_data
    location_name = entry.data.get(CONF_LOCATION_NAME, "百度天气")

    entities: list[SensorEntity] = [
        BaiduWeatherAlertSensor(coordinator, entry, location_name),
        BaiduWeatherAqiSensor(coordinator, entry, location_name),
    ]

    # Create daily forecast sensors (today + next 4 days = 5 sensors)
    for day_index in range(5):
        entities.append(
            BaiduWeatherDailyForecastSensor(
                coordinator, entry, location_name, day_index
            )
        )

    async_add_entities(entities)


class BaiduWeatherAlertSensor(
    CoordinatorEntity[BaiduWeatherCoordinator], SensorEntity
):
    """Sensor entity for weather alerts."""

    _attr_has_entity_name = True
    _attr_translation_key = "weather_alert"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BaiduWeatherCoordinator,
        entry: ConfigEntry,
        location_name: str,
    ) -> None:
        """Initialize the alert sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_alert"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="百度地图",
            name=f"百度天气 - {location_name}",
            configuration_url="https://lbsyun.baidu.com/",
        )

    @property
    def native_value(self) -> str | None:
        """Return the number of active alerts or 'None'."""
        if self.coordinator.data is None:
            return None
        alerts = self.coordinator.data.get(KEY_ALERTS, [])
        if not alerts:
            return "无预警"
        return f"{len(alerts)}条预警"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed alert information."""
        attrs: dict[str, Any] = {}
        if self.coordinator.data is None:
            return attrs

        alerts = self.coordinator.data.get(KEY_ALERTS, [])
        attrs["alert_count"] = len(alerts)
        attrs["alerts"] = []

        for i, alert in enumerate(alerts):
            alert_info = {
                "type": alert.get("type", "未知"),
                "level": alert.get("level", "未知"),
                "title": alert.get("title", ""),
                "description": alert.get("desc", ""),
            }
            attrs["alerts"].append(alert_info)

            # Also expose top-level attributes for voice assistant readability
            if i == 0:
                attrs["alert_type"] = alert.get("type", "未知")
                attrs["alert_level"] = alert.get("level", "未知")
                attrs["alert_title"] = alert.get("title", "")
                attrs["alert_description"] = alert.get("desc", "")

        return attrs


class BaiduWeatherAqiSensor(
    CoordinatorEntity[BaiduWeatherCoordinator], SensorEntity
):
    """Sensor entity for Air Quality Index."""

    _attr_has_entity_name = True
    _attr_translation_key = "aqi"
    _attr_icon = "mdi:air-filter"
    _attr_attribution = ATTRIBUTION
    _attr_state_class = "measurement"

    def __init__(
        self,
        coordinator: BaiduWeatherCoordinator,
        entry: ConfigEntry,
        location_name: str,
    ) -> None:
        """Initialize the AQI sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_aqi"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="百度地图",
            name=f"百度天气 - {location_name}",
            configuration_url="https://lbsyun.baidu.com/",
        )

    @property
    def native_value(self) -> int | None:
        """Return the AQI value."""
        if self.coordinator.data is None:
            return None
        now = self.coordinator.data.get("now", {})
        return now.get("aqi")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed air quality data."""
        attrs: dict[str, Any] = {}
        if self.coordinator.data is None:
            return attrs

        now = self.coordinator.data.get("now", {})
        if now.get("pm25") is not None:
            attrs["pm25"] = now["pm25"]
        if now.get("pm10") is not None:
            attrs["pm10"] = now["pm10"]
        if now.get("no2") is not None:
            attrs["no2"] = now["no2"]
        if now.get("so2") is not None:
            attrs["so2"] = now["so2"]
        if now.get("o3") is not None:
            attrs["o3"] = now["o3"]
        if now.get("co") is not None:
            attrs["co"] = now["co"]

        # AQI level description
        aqi = now.get("aqi")
        if aqi is not None:
            if aqi <= 50:
                attrs["aqi_level"] = "优"
            elif aqi <= 100:
                attrs["aqi_level"] = "良"
            elif aqi <= 150:
                attrs["aqi_level"] = "轻度污染"
            elif aqi <= 200:
                attrs["aqi_level"] = "中度污染"
            elif aqi <= 300:
                attrs["aqi_level"] = "重度污染"
            else:
                attrs["aqi_level"] = "严重污染"

        return attrs


class BaiduWeatherDailyForecastSensor(
    CoordinatorEntity[BaiduWeatherCoordinator], SensorEntity
):
    """Sensor entity for a single day's weather forecast.

    Each instance represents one day (today, tomorrow, day after tomorrow, etc.).
    The sensor state is a human-readable summary like "多云 12~20°C".
    Extra attributes contain detailed forecast fields so that voice assistants
    and LLM integrations can read the forecast directly from entity state.
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-partly-cloudy"
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BaiduWeatherCoordinator,
        entry: ConfigEntry,
        location_name: str,
        day_index: int,
    ) -> None:
        """Initialize the daily forecast sensor.

        Args:
            day_index: 0 = today, 1 = tomorrow, 2 = day after tomorrow, etc.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._day_index = day_index
        self._attr_translation_key = _DAY_KEYS[day_index]
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{_DAY_KEYS[day_index]}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="百度地图",
            name=f"百度天气 - {location_name}",
            configuration_url="https://lbsyun.baidu.com/",
        )

    def _get_forecast_data(self) -> dict[str, Any] | None:
        """Get the forecast data for this day by index."""
        if self.coordinator.data is None:
            return None
        forecasts = self.coordinator.data.get(KEY_FORECASTS, [])
        if self._day_index < len(forecasts):
            return forecasts[self._day_index]
        return None

    @property
    def native_value(self) -> str | None:
        """Return a human-readable weather summary for this day.

        Format: "多云 12~20°C" or "晴转多云 8~18°C"
        This makes it easy for voice assistants to read aloud.
        """
        fc = self._get_forecast_data()
        if fc is None:
            return None

        text_day = fc.get("text_day", "")
        text_night = fc.get("text_night", "")
        high = fc.get("high")
        low = fc.get("low")

        # Build condition text
        if text_day and text_night and text_day != text_night:
            condition_text = f"{text_day}转{text_night}"
        elif text_day:
            condition_text = text_day
        elif text_night:
            condition_text = text_night
        else:
            condition_text = "未知"

        # Build temperature range
        if low is not None and high is not None:
            temp_text = f"{low}~{high}°C"
        elif high is not None:
            temp_text = f"最高{high}°C"
        elif low is not None:
            temp_text = f"最低{low}°C"
        else:
            temp_text = ""

        if temp_text:
            return f"{condition_text} {temp_text}"
        return condition_text

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed forecast attributes for this day.

        These attributes are designed to be easily readable by LLM integrations.
        """
        attrs: dict[str, Any] = {}
        fc = self._get_forecast_data()
        if fc is None:
            return attrs

        # Date
        if fc.get("date"):
            attrs["date"] = fc["date"]

        # Day label (今天/明天/后天...)
        attrs["day_label"] = _DAY_LABELS_CN[self._day_index]

        # Conditions
        if fc.get("text_day"):
            attrs["condition_day"] = fc["text_day"]
        if fc.get("text_night"):
            attrs["condition_night"] = fc["text_night"]

        # Temperatures
        if fc.get("high") is not None:
            attrs["temperature_high"] = fc["high"]
        if fc.get("low") is not None:
            attrs["temperature_low"] = fc["low"]

        # Wind - Day
        if fc.get("wc_day"):
            attrs["wind_class_day"] = fc["wc_day"]
        if fc.get("wd_day"):
            attrs["wind_direction_day"] = fc["wd_day"]

        # Wind - Night
        if fc.get("wc_night"):
            attrs["wind_class_night"] = fc["wc_night"]
        if fc.get("wd_night"):
            attrs["wind_direction_night"] = fc["wd_night"]

        return attrs
