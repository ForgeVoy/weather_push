# -*- coding: utf-8 -*-
"""
每日天气提醒 → 微信推送（Server酱）
天气源: Open-Meteo（免费、无需注册、无需 API Key）
推送:   Server酱（https://sct.ftqq.com，免费每天 5 条，够用）

用法:
  1. 把下面的 SENDKEY 换成你自己的（sct.ftqq.com 微信扫码登录后获取，SCT 开头）
  2. 把 LOCATION 换成你的城市和经纬度
  3. python weather_push.py
"""

import json
import os
import urllib.request
import urllib.parse

# ====== 配置区（GitHub Actions 可用环境变量覆盖）======
SENDKEY = os.environ.get("SCT_SENDKEY", "SCTxxxxxxxxxxxx")
CITY = os.environ.get("WEATHER_CITY", "北京")
LAT = float(os.environ.get("WEATHER_LAT", "39.9042"))
LON = float(os.environ.get("WEATHER_LON", "116.4074"))
# ======================================================


# Open-Meteo 天气代码 → 中文描述
WMO_CODE = {
    0: "晴", 1: "基本晴", 2: "多云", 3: "阴",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨(小)", 67: "冻雨(大)",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "小阵雨", 81: "阵雨", 82: "强阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷雨伴冰雹",
}


def get_weather(lat, lon):
    """从 Open-Meteo 获取今天和明天的天气"""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max",
        "timezone": "auto",
        "forecast_days": 2,
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "weather-push/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wdesc(code):
    return WMO_CODE.get(code, f"未知天气(代码{code})")


def build_message(data):
    """拼装 Markdown 消息"""
    cur = data["current"]
    daily = data["daily"]
    now_t = cur["time"]
    today_idx = 0  # forecast_days=2，第一个就是今天

    lines = []
    lines.append(f"### {CITY} 天气提醒\n")
    lines.append(f"**当前** ({now_t})：{wdesc(cur['weather_code'])}，"
                 f"{cur['temperature_2m']}°C，湿度 {cur['relative_humidity_2m']}%，"
                 f"风速 {cur['wind_speed_10m']} km/h\n")

    for i, date in enumerate(daily["time"]):
        tag = "今天" if i == 0 else "明天"
        hi = daily["temperature_2m_max"][i]
        lo = daily["temperature_2m_min"][i]
        pp = daily["precipitation_probability_max"][i]
        uv = daily["uv_index_max"][i]
        wc = wdesc(daily["weather_code"][i])
        lines.append(f"- **{tag}**（{date}）：{wc}，{lo}~{hi}°C，降水概率 {pp}%，UV指数 {uv}\n")

    # 穿衣/带伞提示
    tips = []
    today_rain = daily["weather_code"][today_idx] in (61, 63, 65, 80, 81, 82, 95, 96, 99, 51, 53, 55)
    tomorrow_rain = daily["weather_code"][1] in (61, 63, 65, 80, 81, 82, 95, 96, 99, 51, 53, 55)
    if today_rain:
        tips.append("☔ 今天有雨，记得带伞")
    if tomorrow_rain:
        tips.append("☂️ 明天有雨，今晚可以把伞放包里")
    if daily["temperature_2m_max"][today_idx] >= 33:
        tips.append("🥵 高温天气，注意防晒补水")
    if daily["temperature_2m_min"][today_idx] <= 3:
        tips.append("🧣 气温较低，注意保暖")
    if daily["uv_index_max"][today_idx] and daily["uv_index_max"][today_idx] >= 7:
        tips.append("🧴 UV 较强，建议防晒")
    if tips:
        lines.append("\n**温馨提示**\n")
        for t in tips:
            lines.append(f"- {t}\n")
    else:
        lines.append("\n今天天气还不错 🙂\n")

    return f"{CITY} | " + wdesc(daily["weather_code"][today_idx]), "".join(lines)


def send_wechat(sendkey, title, desp):
    """通过 Server酱 推送到微信"""
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    payload = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(url, data=payload)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result


def main():
    if SENDKEY.startswith("SCTxxx"):
        print("请先在脚本顶部填入你的 Server酱 SendKey！")
        print("获取地址: https://sct.ftqq.com/sendkey （微信扫码登录即可）")
        return

    data = get_weather(LAT, LON)
    title, desp = build_message(data)
    print("推送标题:", title)
    print("推送内容:\n", desp)
    result = send_wechat(SENDKEY, title, desp)
    if result.get("code") == 0:
        print("\n✅ 推送成功，请查看微信！")
    else:
        print("\n❌ 推送失败:", result)


if __name__ == "__main__":
    main()
