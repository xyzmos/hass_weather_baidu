"""API client for Baidu Weather service."""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import os
from typing import Any

import aiohttp

from .const import (
    ABNORMAL_INT,
    ABNORMAL_STR,
    BAIDU_WEATHER_API,
    DATA_TYPE_ALL,
)

_LOGGER = logging.getLogger(__name__)


class BaiduWeatherApiError(Exception):
    """Base exception for Baidu Weather API errors."""


class BaiduWeatherAuthError(BaiduWeatherApiError):
    """Authentication error."""


class BaiduWeatherConnectionError(BaiduWeatherApiError):
    """Connection error."""


class BaiduWeatherApiClient:
    """Client for the Baidu Weather API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        ak: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._ak = ak

    async def async_get_weather_by_district(
        self, district_id: str, data_type: str = DATA_TYPE_ALL
    ) -> dict[str, Any]:
        """Get weather data by district ID."""
        params = {
            "district_id": district_id,
            "data_type": data_type,
            "ak": self._ak,
            "output": "json",
        }
        return await self._async_request(params)

    async def async_get_weather_by_location(
        self,
        longitude: float,
        latitude: float,
        data_type: str = DATA_TYPE_ALL,
        coordtype: str = "wgs84",
    ) -> dict[str, Any]:
        """Get weather data by longitude and latitude.

        Note: Baidu API expects location format as "longitude,latitude"
        (经度在前，纬度在后).
        """
        params = {
            "location": f"{longitude},{latitude}",
            "data_type": data_type,
            "ak": self._ak,
            "output": "json",
            "coordtype": coordtype,
        }
        return await self._async_request(params)

    async def async_validate_ak(self) -> bool:
        """Validate the API key by making a test request."""
        try:
            params = {
                "district_id": "110100",  # 北京市
                "data_type": "now",
                "ak": self._ak,
                "output": "json",
            }
            await self._async_request(params)
            return True
        except BaiduWeatherAuthError:
            return False
        except BaiduWeatherApiError:
            raise

    async def _async_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make API request and handle response."""
        try:
            async with asyncio.timeout(30):
                response = await self._session.get(
                    BAIDU_WEATHER_API, params=params
                )
                response.raise_for_status()
                data = await response.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise BaiduWeatherConnectionError(
                "请求百度天气API超时"
            ) from err
        except aiohttp.ClientError as err:
            raise BaiduWeatherConnectionError(
                f"连接百度天气API失败: {err}"
            ) from err

        status = data.get("status")
        if status != 0:
            message = data.get("message", "未知错误")
            if status in (1, 2, 3, 4, 5, 200, 201, 202, 211, 220, 240):
                # Auth related errors
                raise BaiduWeatherAuthError(
                    f"百度天气API认证失败 (状态码: {status}): {message}"
                )
            raise BaiduWeatherApiError(
                f"百度天气API请求失败 (状态码: {status}): {message}"
            )

        result = data.get("result", {})
        return self._clean_data(result)

    def _clean_data(self, data: Any) -> Any:
        """Clean abnormal values from API response."""
        if isinstance(data, dict):
            return {k: self._clean_data(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._clean_data(item) for item in data]
        if data == ABNORMAL_INT:
            return None
        if data == ABNORMAL_STR:
            return None
        return data


def load_district_data_from_csv(
    csv_path: str | None = None,
) -> dict[str, dict[str, dict[str, str]]]:
    """Load and parse the district ID CSV data from local file.

    CSV format: district_id,province,city,city_geocode,district,district_geocode,lon,lat

    Returns a nested dict: {province: {city: {district: district_id}}}
    """
    if csv_path is None:
        # Default: look for CSV in the integration directory
        csv_path = os.path.join(
            os.path.dirname(__file__), "weather_district_id.csv"
        )

    districts: dict[str, dict[str, dict[str, str]]] = {}

    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)

            for row in reader:
                if len(row) < 5:
                    continue
                # CSV columns: 0=district_id, 1=province, 2=city,
                #              3=city_geocode, 4=district, 5=district_geocode,
                #              6=lon, 7=lat
                district_id = row[0].strip()
                province = row[1].strip()
                city = row[2].strip()
                district = row[4].strip()

                if not district_id or not province or not district:
                    continue
                districts.setdefault(province, {}).setdefault(city, {})[
                    district
                ] = district_id
    except FileNotFoundError:
        _LOGGER.error("行政区划数据文件未找到: %s", csv_path)
    except Exception as err:
        _LOGGER.error("解析行政区划数据文件失败: %s", err)

    return districts
