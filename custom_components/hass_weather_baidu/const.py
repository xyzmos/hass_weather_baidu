"""Constants for the Baidu Weather integration."""

from datetime import timedelta

DOMAIN = "hass_weather_baidu"

# Configuration keys
CONF_AK = "ak"
CONF_MODE = "mode"
CONF_DISTRICT_ID = "district_id"
CONF_LOCATION_NAME = "location_name"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PROVINCE = "province"
CONF_CITY = "city"
CONF_DISTRICT = "district"

# Mode values
MODE_DISTRICT = "district"
MODE_LOCATION = "location"

# API
BAIDU_WEATHER_API = "https://api.map.baidu.com/weather/v1/"

# Default values
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=15)
DEFAULT_NAME = "百度天气"

# Data types for API
DATA_TYPE_ALL = "all"
DATA_TYPE_NOW = "now"
DATA_TYPE_FORECAST = "fc"
DATA_TYPE_FORECAST_HOUR = "fc_hour"
DATA_TYPE_ALERT = "alert"
DATA_TYPE_INDEX = "index"

# Coordinator data keys
KEY_NOW = "now"
KEY_FORECASTS = "forecasts"
KEY_FORECAST_HOURS = "forecast_hours"
KEY_ALERTS = "alerts"
KEY_INDEXES = "indexes"
KEY_LOCATION = "location"

# Platforms
PLATFORMS = ["weather", "sensor"]

# Abnormal values from API
ABNORMAL_INT = 999999
ABNORMAL_STR = "暂无"

# Baidu weather condition to HA condition mapping
CONDITION_MAP: dict[str, str] = {
    "晴": "sunny",
    "多云": "partlycloudy",
    "阴": "cloudy",
    "阵雨": "rainy",
    "雷阵雨": "lightning-rainy",
    "雷阵雨伴有冰雹": "hail",
    "雨夹雪": "snowy-rainy",
    "小雨": "rainy",
    "中雨": "rainy",
    "大雨": "pouring",
    "暴雨": "pouring",
    "大暴雨": "pouring",
    "特大暴雨": "pouring",
    "阵雪": "snowy",
    "小雪": "snowy",
    "中雪": "snowy",
    "大雪": "snowy",
    "暴雪": "snowy",
    "雾": "fog",
    "冻雨": "snowy-rainy",
    "沙尘暴": "exceptional",
    "小到中雨": "rainy",
    "中到大雨": "rainy",
    "大到暴雨": "pouring",
    "暴雨到大暴雨": "pouring",
    "大暴雨到特大暴雨": "pouring",
    "小到中雪": "snowy",
    "中到大雪": "snowy",
    "大到暴雪": "snowy",
    "浮尘": "exceptional",
    "扬沙": "exceptional",
    "强沙尘暴": "exceptional",
    "霾": "fog",
    "小雨-中雨": "rainy",
    "中雨-大雨": "rainy",
    "大雨-暴雨": "pouring",
    "暴雨-大暴雨": "pouring",
    "大暴雨-特大暴雨": "pouring",
    "小雪-中雪": "snowy",
    "中雪-大雪": "snowy",
    "大雪-暴雪": "snowy",
}

# Wind class to speed mapping (km/h, approximate midpoint)
WIND_SPEED_MAP: dict[str, float] = {
    "微风": 5.0,
    "和风": 15.0,
    "清风": 25.0,
    "<3级": 9.0,
    "1级": 2.0,
    "2级": 7.0,
    "3级": 14.0,
    "4级": 22.0,
    "5级": 32.0,
    "6级": 42.0,
    "7级": 54.0,
    "8级": 67.0,
    "9级": 81.0,
    "10级": 96.0,
    "11级": 112.0,
    "12级": 130.0,
}

# Wind direction to bearing mapping
WIND_BEARING_MAP: dict[str, float] = {
    "北风": 0.0,
    "东北风": 45.0,
    "东风": 90.0,
    "东南风": 135.0,
    "南风": 180.0,
    "西南风": 225.0,
    "西风": 270.0,
    "西北风": 315.0,
}

# Attribution
ATTRIBUTION = "数据来源：百度地图天气服务"
