"""Fixtures and mock data for Baidu Weather tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from homeassistant.core import HomeAssistant

MOCK_AK = "test_ak_key_123456"

MOCK_WEATHER_RESPONSE = {
    "status": 0,
    "result": {
        "location": {
            "country": "中国",
            "province": "北京市",
            "city": "北京市",
            "name": "海淀区",
            "id": "110108",
        },
        "now": {
            "temp": 25,
            "feels_like": 27,
            "rh": 60,
            "wind_class": "3级",
            "wind_dir": "南风",
            "text": "晴",
            "prec_1h": 0.0,
            "clouds": 20,
            "vis": 10000,
            "aqi": 75,
            "pm25": 35,
            "pm10": 50,
            "no2": 20,
            "so2": 5,
            "o3": 100,
            "co": 0.5,
            "uptime": "2026-02-12 14:00",
        },
        "forecasts": [
            {
                "date": "2026-02-12",
                "week": "星期四",
                "high": 28,
                "low": 18,
                "wc_day": "3级",
                "wc_night": "2级",
                "wd_day": "南风",
                "wd_night": "北风",
                "text_day": "晴",
                "text_night": "多云",
            },
            {
                "date": "2026-02-13",
                "week": "星期五",
                "high": 26,
                "low": 16,
                "wc_day": "4级",
                "wc_night": "3级",
                "wd_day": "东南风",
                "wd_night": "东风",
                "text_day": "多云",
                "text_night": "小雨",
            },
        ],
        "forecast_hours": [
            {
                "text": "晴",
                "temp_fc": 25,
                "wind_class": "3级",
                "wind_dir": "南风",
                "rh": 60,
                "prec_1h": 0.0,
                "clouds": 20,
                "data_time": "2026-02-12 15:00",
            },
            {
                "text": "多云",
                "temp_fc": 24,
                "wind_class": "2级",
                "wind_dir": "南风",
                "rh": 65,
                "prec_1h": 0.0,
                "clouds": 40,
                "data_time": "2026-02-12 16:00",
            },
        ],
        "alerts": [
            {
                "type": "大风",
                "level": "蓝色",
                "title": "北京市气象台发布大风蓝色预警",
                "desc": "预计未来24小时将出现5-6级大风。",
            }
        ],
        "indexes": [
            {
                "name": "紫外线指数",
                "brief": "强",
                "detail": "紫外线辐射强，建议涂擦SPF20左右的防晒霜。",
            }
        ],
    },
}

MOCK_DISTRICT_CSV = """district_id,province,city,district
110100,北京市,北京市,东城区
110101,北京市,北京市,西城区
110108,北京市,北京市,海淀区
310100,上海市,上海市,黄浦区
310101,上海市,上海市,徐汇区
"""
