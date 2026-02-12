# 百度天气 - Home Assistant 自定义集成

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/xyzmos/hass_weather_baidu.svg)](https://github.com/xyzmos/hass_weather_baidu/releases)
[![License](https://img.shields.io/github/license/xyzmos/hass_weather_baidu.svg)](LICENSE)

基于百度地图天气服务的 Home Assistant 天气集成插件，支持获取实时天气、逐小时预报、7天预报及气象预警信息。

## ✨ 功能特性

- 🌤️ **实时天气**：温度、体感温度、湿度、风速、风向、云量、能见度、气压等
- 📊 **逐小时预报**：未来24小时逐小时天气预报
- 📅 **7天预报**：未来7天每日天气预报
- ⚠️ **气象预警**：独立传感器实体，实时推送预警信息
- 🌬️ **空气质量**：AQI、PM2.5、PM10、NO₂、SO₂、O₃、CO
- 🗣️ **语音助手支持**：所有关键属性均可被语音助手读取
- 🌐 **多语言支持**：支持中文和英文界面
- 🔧 **双配置模式**：
  - 按行政区划代码选择（省/市/区县级联）
  - 按 Home Assistant 地点经纬度选择

## 📋 前置要求

1. 百度地图开放平台账号
2. 天气服务 API Key（AK）— 在[百度地图开放平台 API 控制台](https://lbsyun.baidu.com/apiconsole/key)申请

## 📦 安装方式

### HACS 安装（推荐）

1. 打开 HACS
2. 点击右上角 **⋮** > **自定义存储库**
3. 添加仓库地址：`https://github.com/xyzmos/hass_weather_baidu`
4. 类别选择：**集成**
5. 搜索 **百度天气** 并安装
6. 重启 Home Assistant

### 手动安装

1. 下载最新 [Release](https://github.com/xyzmos/hass_weather_baidu/releases)
2. 将 `custom_components/hass_weather_baidu` 文件夹复制到你的 HA 配置目录下的 `custom_components/` 目录
3. 重启 Home Assistant

## ⚙️ 配置

### 通过 UI 配置

1. 进入 **设置** > **设备与服务** > **添加集成**
2. 搜索 **百度天气**
3. 输入你的百度地图 AK 密钥
4. 选择配置模式：
   - **按行政区划选择**：依次选择省份 → 城市 → 区县
   - **按地点经纬度选择**：从 Home Assistant 已配置的地点列表中选择

### 选项配置

添加集成后，可在选项中调整：

| 选项 | 默认值 | 说明 |
|------|--------|------|
| 更新间隔 | 900秒（15分钟） | 天气数据更新频率，范围 300-7200 秒 |

## 📊 实体说明

### 天气实体 (weather.*)

| 属性 | 说明 |
|------|------|
| temperature | 当前温度 (°C) |
| apparent_temperature | 体感温度 (°C) |
| humidity | 相对湿度 (%) |
| pressure | 气压 (hPa) |
| wind_speed | 风速 (km/h) |
| wind_bearing | 风向角度 |
| cloud_coverage | 云量 (%) |
| visibility | 能见度 (km) |
| ozone | 臭氧浓度 |
| dew_point | 露点温度 |
| uv_index | 紫外线指数 |
| condition | 天气状态 |

**额外属性（extra_state_attributes）：**

| 属性 | 说明 |
|------|------|
| aqi | 空气质量指数 |
| pm25 | PM2.5 浓度 |
| pm10 | PM10 浓度 |
| condition_cn | 中文天气描述 |
| wind_class | 风力等级 |
| wind_direction_cn | 中文风向 |
| precipitation_1h | 1小时累计降水量 |
| update_time | 数据更新时间 |

### 预警传感器 (sensor.*_weather_alert)

| 属性 | 说明 |
|------|------|
| state | 预警数量描述 |
| alert_count | 预警条数 |
| alert_type | 首条预警类型 |
| alert_level | 首条预警等级 |
| alert_title | 首条预警标题 |
| alert_description | 首条预警详情 |
| alerts | 所有预警详情列表 |

### 空气质量传感器 (sensor.*_aqi)

| 属性 | 说明 |
|------|------|
| state | AQI 数值 |
| aqi_level | AQI 等级描述 |
| pm25 | PM2.5 浓度 |
| pm10 | PM10 浓度 |
| no2 | NO₂ 浓度 |
| so2 | SO₂ 浓度 |
| o3 | O₃ 浓度 |
| co | CO 浓度 |

## 🗣️ 语音助手使用

天气实体的所有核心属性（温度、湿度、天气状况等）均可被 Home Assistant 语音助手自动读取。预警与空气质量传感器也可通过语音查询。

示例语音指令：
- "今天天气怎么样？"
- "现在温度多少度？"
- "有没有天气预警？"
- "空气质量怎么样？"

## 🔍 诊断

集成支持 Home Assistant 诊断功能，可在 **设置** > **设备与服务** > **百度天气** > **诊断** 中导出调试信息（AK 密钥会被自动脱敏）。

## 📄 数据来源

天气数据由[百度地图天气服务](https://lbsyun.baidu.com/faq/api?title=webapi/weather/base)提供。

## 📝 许可证

本项目基于 [Apache License 2.0](LICENSE) 许可证开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📌 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
