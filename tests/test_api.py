"""Tests for Baidu Weather API client."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.hass_weather_baidu.api import (
    BaiduWeatherApiClient,
    BaiduWeatherApiError,
    BaiduWeatherAuthError,
    BaiduWeatherConnectionError,
    async_fetch_district_data,
)

from .conftest import MOCK_AK, MOCK_DISTRICT_CSV, MOCK_WEATHER_RESPONSE


class TestBaiduWeatherApiClient:
    """Test BaiduWeatherApiClient."""

    async def test_get_weather_by_district_success(self) -> None:
        """Test successful weather fetch by district ID."""
        session = MagicMock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=MOCK_WEATHER_RESPONSE)
        session.get = AsyncMock(return_value=mock_response)
        session.get.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        session.get.return_value.__aexit__ = AsyncMock(return_value=False)

        client = BaiduWeatherApiClient(session=session, ak=MOCK_AK)

        with patch("asyncio.timeout"):
            result = await client.async_get_weather_by_district("110108")

        assert result is not None
        assert "now" in result or "location" in result

    async def test_get_weather_auth_error(self) -> None:
        """Test auth error handling."""
        session = MagicMock(spec=aiohttp.ClientSession)
        error_response = {"status": 211, "message": "AK无效"}
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=error_response)
        session.get = AsyncMock(return_value=mock_response)

        client = BaiduWeatherApiClient(session=session, ak="invalid_ak")

        with pytest.raises(BaiduWeatherAuthError):
            with patch("asyncio.timeout"):
                await client.async_get_weather_by_district("110108")

    async def test_clean_abnormal_values(self) -> None:
        """Test that abnormal values are cleaned."""
        session = MagicMock(spec=aiohttp.ClientSession)
        response_data = {
            "status": 0,
            "result": {
                "now": {
                    "temp": 25,
                    "pressure": 999999,
                    "wind_class": "暂无",
                }
            },
        }
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=response_data)
        session.get = AsyncMock(return_value=mock_response)

        client = BaiduWeatherApiClient(session=session, ak=MOCK_AK)

        with patch("asyncio.timeout"):
            result = await client.async_get_weather_by_district("110108")

        assert result["now"]["temp"] == 25
        assert result["now"]["pressure"] is None
        assert result["now"]["wind_class"] is None


class TestAsyncFetchDistrictData:
    """Test district data fetching."""

    async def test_parse_district_csv(self) -> None:
        """Test CSV parsing returns correct structure."""
        session = MagicMock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=MOCK_DISTRICT_CSV)
        session.get = AsyncMock(return_value=mock_response)

        with patch("asyncio.timeout"):
            result = await async_fetch_district_data(session)

        assert "北京市" in result
        assert "北京市" in result["北京市"]
        assert "海淀区" in result["北京市"]["北京市"]
        assert result["北京市"]["北京市"]["海淀区"] == "110108"

        assert "上海市" in result
        assert "黄浦区" in result["上海市"]["上海市"]
