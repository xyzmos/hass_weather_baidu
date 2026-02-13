"""Weather entity for Baidu Weather integration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONDITION_MAP,
    CONF_LOCATION_NAME,
    DOMAIN,
    KEY_ALERTS,
    KEY_FORECAST_HOURS,
    KEY_FORECASTS,
    KEY_INDEXES,
    KEY_NOW,
    WIND_BEARING_MAP,
    WIND_SPEED_MAP,
)
from .coordinator import BaiduWeatherCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Baidu Weather entity from a config entry."""
    coordinator: BaiduWeatherCoordinator = entry.runtime_data
    async_add_entities([BaiduWeatherEntity(coordinator, entry)])


class BaiduWeatherEntity(CoordinatorEntity[BaiduWeatherCoordinator], WeatherEntity):
    """Representation of a Baidu Weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_attribution = ATTRIBUTION

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY
        | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self,
        coordinator: BaiduWeatherCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._entry = entry
        location_name = entry.data.get(CONF_LOCATION_NAME, "百度天气")

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="百度地图",
            name=f"百度天气 - {location_name}",
            configuration_url="https://lbsyun.baidu.com/",
        )

    @property
    def _now_data(self) -> dict[str, Any]:
        """Return current weather data."""
        if self.coordinator.data is None:
            return {}
        return self.coordinator.data.get(KEY_NOW, {})

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        text = self._now_data.get("text")
        if text is None:
            return None
        return CONDITION_MAP.get(text, "exceptional")

    @property
    def native_temperature(self) -> float | None:
        """Return the temperature."""
        return self._now_data.get("temp")

    @property
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature."""
        return self._now_data.get("feels_like")

    @property
    def humidity(self) -> float | None:
        """Return the humidity."""
        return self._now_data.get("rh")

    @property
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        return self._now_data.get("pressure")

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        wind_class = self._now_data.get("wind_class")
        if wind_class is None:
            return None
        return WIND_SPEED_MAP.get(wind_class)

    @property
    def wind_bearing(self) -> float | str | None:
        """Return the wind bearing."""
        wind_dir = self._now_data.get("wind_dir")
        if wind_dir is None:
            return None
        # Try numeric angle first
        wind_angle = self._now_data.get("wind_angle")
        if wind_angle is not None:
            return float(wind_angle)
        return WIND_BEARING_MAP.get(wind_dir, wind_dir)

    @property
    def cloud_coverage(self) -> float | None:
        """Return the cloud coverage."""
        return self._now_data.get("clouds")

    @property
    def native_visibility(self) -> float | None:
        """Return visibility in km."""
        vis = self._now_data.get("vis")
        if vis is None:
            return None
        # API returns meters, convert to km
        return vis / 1000.0

    @property
    def native_visibility_unit(self) -> str:
        """Return the visibility unit."""
        return UnitOfLength.KILOMETERS

    @property
    def ozone(self) -> float | None:
        """Return the ozone level."""
        return self._now_data.get("o3")

    @property
    def native_dew_point(self) -> float | None:
        """Return the dew point."""
        return self._now_data.get("dpt")

    @property
    def uv_index(self) -> float | None:
        """Return the UV index."""
        return self._now_data.get("uvi")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes for voice assistants.

        Includes forecast data so that LLM integrations (e.g. Extended OpenAI
        Conversation) can read forecasts directly from entity state without
        needing to call the weather.get_forecasts service (which requires
        return_response=True that many LLM integrations don't support).
        """
        attrs: dict[str, Any] = {}
        now = self._now_data

        if now.get("aqi") is not None:
            attrs["aqi"] = now["aqi"]
        if now.get("pm25") is not None:
            attrs["pm25"] = now["pm25"]
        if now.get("pm10") is not None:
            attrs["pm10"] = now["pm10"]
        if now.get("no2") is not None:
            attrs["no2"] = now["no2"]
        if now.get("so2") is not None:
            attrs["so2"] = now["so2"]
        if now.get("co") is not None:
            attrs["co"] = now["co"]
        if now.get("prec_1h") is not None:
            attrs["precipitation_1h"] = now["prec_1h"]
        if now.get("text") is not None:
            attrs["condition_cn"] = now["text"]
        if now.get("wind_class") is not None:
            attrs["wind_class"] = now["wind_class"]
        if now.get("wind_dir") is not None:
            attrs["wind_direction_cn"] = now["wind_dir"]
        if now.get("uptime") is not None:
            attrs["update_time"] = now["uptime"]

        # --- Daily forecast (for voice assistants / LLM) ---
        if self.coordinator.data is not None:
            forecasts_raw = self.coordinator.data.get(KEY_FORECASTS, [])
            if forecasts_raw:
                forecast_list = []
                for fc in forecasts_raw:
                    date_str = fc.get("date", "")
                    entry: dict[str, Any] = {"date": date_str}
                    if fc.get("text_day"):
                        entry["condition_day"] = fc["text_day"]
                    if fc.get("text_night"):
                        entry["condition_night"] = fc["text_night"]
                    if fc.get("high") is not None:
                        entry["temperature_high"] = fc["high"]
                    if fc.get("low") is not None:
                        entry["temperature_low"] = fc["low"]
                    if fc.get("wc_day"):
                        entry["wind_class_day"] = fc["wc_day"]
                    if fc.get("wd_day"):
                        entry["wind_direction_day"] = fc["wd_day"]
                    if fc.get("wc_night"):
                        entry["wind_class_night"] = fc["wc_night"]
                    if fc.get("wd_night"):
                        entry["wind_direction_night"] = fc["wd_night"]
                    forecast_list.append(entry)
                attrs["forecast_daily"] = forecast_list

            # --- Hourly forecast ---
            hours_raw = self.coordinator.data.get(KEY_FORECAST_HOURS, [])
            if hours_raw:
                hourly_list = []
                for hour in hours_raw:
                    entry = {}
                    if hour.get("data_time"):
                        entry["datetime"] = hour["data_time"]
                    if hour.get("text"):
                        entry["condition"] = hour["text"]
                    if hour.get("temp_fc") is not None:
                        entry["temperature"] = hour["temp_fc"]
                    if hour.get("rh") is not None:
                        entry["humidity"] = hour["rh"]
                    if hour.get("wind_class"):
                        entry["wind_class"] = hour["wind_class"]
                    if hour.get("wind_dir"):
                        entry["wind_direction"] = hour["wind_dir"]
                    if hour.get("prec_1h") is not None:
                        entry["precipitation"] = hour["prec_1h"]
                    hourly_list.append(entry)
                attrs["forecast_hourly"] = hourly_list

            # --- Weather alerts ---
            alerts = self.coordinator.data.get(KEY_ALERTS, [])
            if alerts:
                alert_list = []
                for alert in alerts:
                    entry = {}
                    if alert.get("title"):
                        entry["title"] = alert["title"]
                    if alert.get("type"):
                        entry["type"] = alert["type"]
                    if alert.get("level"):
                        entry["level"] = alert["level"]
                    if alert.get("desc"):
                        entry["description"] = alert["desc"]
                    alert_list.append(entry)
                attrs["alerts"] = alert_list

            # --- Life indexes ---
            indexes = self.coordinator.data.get(KEY_INDEXES, [])
            if indexes:
                index_list = []
                for idx in indexes:
                    entry = {}
                    if idx.get("name"):
                        entry["name"] = idx["name"]
                    if idx.get("brief"):
                        entry["brief"] = idx["brief"]
                    if idx.get("detail"):
                        entry["detail"] = idx["detail"]
                    index_list.append(entry)
                attrs["life_indexes"] = index_list

        return attrs

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        if self.coordinator.data is None:
            return None

        forecasts_raw = self.coordinator.data.get(KEY_FORECASTS, [])
        if not forecasts_raw:
            return None

        forecasts: list[Forecast] = []
        for fc in forecasts_raw:
            date_str = fc.get("date")
            if not date_str:
                continue

            # Parse date to RFC3339 format
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dt_str = dt.strftime("%Y-%m-%dT00:00:00+08:00")
            except (ValueError, TypeError):
                dt_str = date_str

            condition_day = fc.get("text_day")
            condition = CONDITION_MAP.get(condition_day, "exceptional") if condition_day else None

            wind_speed = None
            wc_day = fc.get("wc_day")
            if wc_day:
                wind_speed = WIND_SPEED_MAP.get(wc_day)

            wind_bearing = None
            wd_day = fc.get("wd_day")
            if wd_day:
                wind_bearing = WIND_BEARING_MAP.get(wd_day)

            forecast = Forecast(
                datetime=dt_str,
                condition=condition,
                native_temperature=fc.get("high"),
                native_templow=fc.get("low"),
                native_wind_speed=wind_speed,
                wind_bearing=wind_bearing,
            )
            forecasts.append(forecast)

        return forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast."""
        if self.coordinator.data is None:
            return None

        hours_raw = self.coordinator.data.get(KEY_FORECAST_HOURS, [])
        if not hours_raw:
            return None

        forecasts: list[Forecast] = []
        for hour in hours_raw:
            data_time = hour.get("data_time")
            if not data_time:
                continue

            # Parse time to RFC3339
            try:
                # data_time format is like "2024-01-01 12:00"
                dt = datetime.strptime(data_time, "%Y-%m-%d %H:%M")
                dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")
            except (ValueError, TypeError):
                dt_str = data_time

            text = hour.get("text")
            condition = CONDITION_MAP.get(text, "exceptional") if text else None

            wind_speed = None
            wc = hour.get("wind_class")
            if wc:
                wind_speed = WIND_SPEED_MAP.get(wc)

            wind_bearing = None
            wd = hour.get("wind_dir")
            if wd:
                wind_angle = hour.get("wind_angle")
                if wind_angle is not None:
                    wind_bearing = float(wind_angle)
                else:
                    wind_bearing = WIND_BEARING_MAP.get(wd)

            forecast = Forecast(
                datetime=dt_str,
                condition=condition,
                native_temperature=hour.get("temp_fc"),
                humidity=hour.get("rh"),
                cloud_coverage=hour.get("clouds"),
                native_precipitation=hour.get("prec_1h"),
                native_wind_speed=wind_speed,
                wind_bearing=wind_bearing,
                precipitation_probability=hour.get("pop"),
                uv_index=hour.get("uvi"),
                native_pressure=hour.get("pressure"),
                native_dew_point=hour.get("dpt"),
            )
            forecasts.append(forecast)

        return forecasts
