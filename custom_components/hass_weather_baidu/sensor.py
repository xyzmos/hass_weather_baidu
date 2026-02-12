"""Sensor entities for Baidu Weather integration - Weather Alerts."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_LOCATION_NAME,
    DOMAIN,
    KEY_ALERTS,
    KEY_INDEXES,
)
from .coordinator import BaiduWeatherCoordinator

_LOGGER = logging.getLogger(__name__)


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
