"""Config flow for Baidu Weather integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    BaiduWeatherApiClient,
    BaiduWeatherApiError,
    BaiduWeatherAuthError,
    BaiduWeatherConnectionError,
    load_district_data_from_csv,
)
from .const import (
    CONF_AK,
    CONF_CITY,
    CONF_DISTRICT,
    CONF_DISTRICT_ID,
    CONF_LATITUDE,
    CONF_LOCATION_NAME,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_PROVINCE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MODE_DISTRICT,
    MODE_LOCATION,
)

_LOGGER = logging.getLogger(__name__)


class BaiduWeatherConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baidu Weather."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._ak: str = ""
        self._mode: str = ""
        self._districts: dict[str, dict[str, dict[str, str]]] = {}
        self._province: str = ""
        self._city: str = ""
        self._district: str = ""
        self._district_id: str = ""
        self._location_name: str = ""
        self._latitude: float = 0.0
        self._longitude: float = 0.0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - enter AK and select mode."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._ak = user_input[CONF_AK]
            self._mode = user_input[CONF_MODE]

            # Validate AK
            session = async_get_clientsession(self.hass)
            client = BaiduWeatherApiClient(session=session, ak=self._ak)
            try:
                valid = await client.async_validate_ak()
                if not valid:
                    errors["base"] = "invalid_ak"
            except BaiduWeatherConnectionError:
                errors["base"] = "cannot_connect"
            except BaiduWeatherApiError:
                errors["base"] = "unknown"

            if not errors:
                if self._mode == MODE_DISTRICT:
                    return await self.async_step_province()
                return await self.async_step_location()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AK): str,
                    vol.Required(CONF_MODE, default=MODE_DISTRICT): vol.In(
                        {
                            MODE_DISTRICT: "按行政区划选择",
                            MODE_LOCATION: "按地点经纬度选择",
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_province(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle province selection step."""
        errors: dict[str, str] = {}

        if not self._districts:
            # Load from local CSV file
            self._districts = await self.hass.async_add_executor_job(
                load_district_data_from_csv
            )
            if not self._districts:
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="province",
                    data_schema=vol.Schema(
                        {vol.Required(CONF_PROVINCE): str}
                    ),
                    errors=errors,
                )

        if user_input is not None:
            self._province = user_input[CONF_PROVINCE]
            return await self.async_step_city()

        provinces = sorted(self._districts.keys())
        return self.async_show_form(
            step_id="province",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROVINCE): vol.In(
                        {p: p for p in provinces}
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_city(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle city selection step."""
        if user_input is not None:
            self._city = user_input[CONF_CITY]
            return await self.async_step_district()

        cities = sorted(self._districts.get(self._province, {}).keys())
        return self.async_show_form(
            step_id="city",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CITY): vol.In({c: c for c in cities}),
                }
            ),
        )

    async def async_step_district(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle district selection step."""
        if user_input is not None:
            self._district = user_input[CONF_DISTRICT]
            self._district_id = (
                self._districts.get(self._province, {})
                .get(self._city, {})
                .get(self._district, "")
            )

            if not self._district_id:
                return self.async_show_form(
                    step_id="district",
                    data_schema=vol.Schema(
                        {vol.Required(CONF_DISTRICT): str}
                    ),
                    errors={"base": "unknown"},
                )

            # Check for duplicate
            await self.async_set_unique_id(
                f"{DOMAIN}_{self._district_id}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{self._province} {self._city} {self._district}",
                data={
                    CONF_AK: self._ak,
                    CONF_MODE: MODE_DISTRICT,
                    CONF_DISTRICT_ID: self._district_id,
                    CONF_PROVINCE: self._province,
                    CONF_CITY: self._city,
                    CONF_DISTRICT: self._district,
                    CONF_LOCATION_NAME: f"{self._city}{self._district}",
                },
            )

        districts_in_city = (
            self._districts.get(self._province, {}).get(self._city, {})
        )
        district_names = sorted(districts_in_city.keys())
        return self.async_show_form(
            step_id="district",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DISTRICT): vol.In(
                        {d: d for d in district_names}
                    ),
                }
            ),
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle location selection step using HA zones."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected = user_input.get("zone")
            if selected == "__home__":
                self._location_name = "Home"
                self._latitude = self.hass.config.latitude
                self._longitude = self.hass.config.longitude
            elif selected == "__manual__":
                # Manual input mode
                lat = user_input.get(CONF_LATITUDE)
                lon = user_input.get(CONF_LONGITUDE)
                name = user_input.get(CONF_LOCATION_NAME, "自定义位置")
                if lat is not None and lon is not None:
                    self._location_name = name
                    self._latitude = float(lat)
                    self._longitude = float(lon)
                else:
                    errors["base"] = "invalid_location"
            else:
                zone = self.hass.states.get(selected)
                if zone:
                    self._location_name = zone.name
                    self._latitude = zone.attributes.get("latitude", 0.0)
                    self._longitude = zone.attributes.get("longitude", 0.0)
                else:
                    errors["base"] = "invalid_location"

            if not errors:
                if self._latitude == 0.0 and self._longitude == 0.0:
                    errors["base"] = "invalid_location"

            if not errors:
                # Validate we can get weather for this location
                session = async_get_clientsession(self.hass)
                client = BaiduWeatherApiClient(session=session, ak=self._ak)
                try:
                    await client.async_get_weather_by_location(
                        longitude=self._longitude,
                        latitude=self._latitude,
                        data_type="now",
                    )
                except BaiduWeatherAuthError:
                    errors["base"] = "invalid_ak"
                except BaiduWeatherConnectionError:
                    errors["base"] = "cannot_connect"
                except BaiduWeatherApiError:
                    errors["base"] = "unknown"

            if not errors:
                # Check for duplicate
                unique = f"{DOMAIN}_{self._latitude}_{self._longitude}"
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"百度天气 - {self._location_name}",
                    data={
                        CONF_AK: self._ak,
                        CONF_MODE: MODE_LOCATION,
                        CONF_LATITUDE: self._latitude,
                        CONF_LONGITUDE: self._longitude,
                        CONF_LOCATION_NAME: self._location_name,
                    },
                )

        # Build zone options - always include Home and manual entry
        zone_options: dict[str, str] = {
            "__home__": f"Home ({self.hass.config.latitude}, {self.hass.config.longitude})"
        }

        # Add configured zones
        for state in self.hass.states.async_all("zone"):
            lat = state.attributes.get("latitude", "")
            lon = state.attributes.get("longitude", "")
            zone_options[state.entity_id] = f"{state.name} ({lat}, {lon})"

        # Add manual option
        zone_options["__manual__"] = "手动输入经纬度"

        schema_fields: dict[Any, Any] = {
            vol.Required("zone", default="__home__"): vol.In(zone_options),
        }

        # Add manual input fields (always shown, only used when __manual__ selected)
        schema_fields[vol.Optional(CONF_LOCATION_NAME)] = str
        schema_fields[vol.Optional(CONF_LATITUDE)] = vol.Coerce(float)
        schema_fields[vol.Optional(CONF_LONGITUDE)] = vol.Coerce(float)

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(schema_fields),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> BaiduWeatherOptionsFlowHandler:
        """Get the options flow for this handler."""
        return BaiduWeatherOptionsFlowHandler()


class BaiduWeatherOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Baidu Weather."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                },
            )

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            int(DEFAULT_UPDATE_INTERVAL.total_seconds()),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=300, max=7200),
                    ),
                }
            ),
        )
