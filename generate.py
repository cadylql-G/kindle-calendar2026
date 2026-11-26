import os
import json
import urllib.request
from datetime import datetime, date, time, timedelta
import pytz
from icalendar import Calendar
import recurring_ical_events

TZ = pytz.timezone("America/Toronto")
ICS_URL = os.environ["GCAL_ICS_URL"].strip()
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=43.77&longitude=-79.26"
    "&current=temperature_2m,weather_code"
    "&daily=temperature_2m_max,temperature_2m_min"
    "&timezone=America%2FToronto&forecast_days=1"
)

WEEKDAYS_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

WEATHER_MAP = {
    0: "晴", 1: "大部晴朗", 2: "多云", 3: "阴天",
    45: "有雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "浓毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "阵雨", 81: "中阵雨", 82: "强阵雨",
    85: "阵雪", 86: "强阵雪",
    95: "雷阵雨", 96: "雷雨伴冰雹", 99: "强雷雨伴冰雹"
}

def get_weather():
    try:
        req = urllib.request.Request(WEATHER_URL, headers={"User-Agent": "KindleCalendar/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cur = data.get("current", {})
        daily = data.get("daily", {})
        temp_now = round(cur["temperature_2m"])
        desc = WEATHER_MAP.get(cur.get("weather_code"), "多云")
        t_min = round(daily["temperature_2m_min"][0])
        t_max = round(daily["temperature_2m_max"][0])
        return f"多伦多 {desc} {temp_now}°C（{t_min}~{t_max}°C）"
    except Exception:
        return "天气暂不可用"

def get_today_events():
    now = datetime.now(TZ)
    today = now.date()
    start_dt = TZ.localize(datetime.combine(today, time.min))
    end_dt = TZ.localize(datetime.combine(today + timedelta(days=1), time.min))

    req = urllib.request.Request(ICS_URL, headers={"User-Agent": "KindleCalendar/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        cal = Calendar.from_ical(resp.read())

    events = recurring_ical_events.of(cal).between(start_dt, end_dt)
    parsed = []

    for ev in events:
        summary = str(ev.get("SUMMARY", "无标题日程")).strip()
        dtstart = ev.get("DTSTART").dt

        if isinstance(dtstart, datetime):
            if dtstart.tzinfo is None:
                dt_local = TZ.localize(dtstart)
            else:
                dt_local = dtstart.astimezone(TZ)
            sort_key = dt_local.strftime("%H:%M")
            time_str = dt_local.strftime("%H:%M")
        elif isinstance(dtstart, date):
            sort_key = "00:00"
            time_str = "全天"
        else:
            continue

        parsed.append((sort_key, time_str, summary))

    parsed.sort(key=lambda x: x[0])
    return parsed

def main():
    now = datetime.now(TZ)
    date_str = f"{now.year}年{now.month}月{now.day}日"
    weekday_str = WEEKDAYS_CN[now.weekday()]
    update_time = now.strftime("%H:%M")
    weather_str = get_weather()
    events = get_today_events()

    if events:
        items_html = "\n".join(
            f'<div class="event"><span class="time">{t}</span><span class="title">{s}</span></div>'
            for _, t, s in events
        )
    else:
        items_html = '<div class="empty">今天没有日程安排</div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="900">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kindle Calendar</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
      margin: 0;
      padding: 26px 34px;
      background: #ffffff;
      color: #000000;
      width: 100vh;
      height: 100vw;
      transform: rotate(90deg);
      transform-origin: top left;
      position: absolute;
      top: 0;
      left: 100vw;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .header {{
      border-bottom: 4px solid #000000;
      padding-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }}
    .date-box .date {{
      font-size: 46px;
      font-weight: 900;
      line-height: 1.1;
      letter-spacing: -0.5px;
    }}
    .date-box .weekday {{
      font-size: 32px;
      font-weight: 700;
      margin-top: 6px;
    }}
    .weather {{
      font-size: 28px;
      font-weight: 700;
      text-align: right;
      line-height: 1.3;
    }}
    .events {{
      flex: 1;
      padding: 18px 0;
      overflow: hidden;
    }}
    .event {{
      display: flex;
      align-items: baseline;
      padding: 10px 0;
      border-bottom: 1px dashed #666666;
      font-size: 34px;
      line-height: 1.25;
    }}
    .event:last-child {{
      border-bottom: none;
    }}
    .event .time {{
      font-weight: 800;
      min-width: 120px;
      display: inline-block;
    }}
    .event .title {{
      font-weight: 600;
    }}
    .empty {{
      font-size: 34px;
      color: #333333;
      margin-top: 36px;
      text-align: center;
    }}
    .footer {{
      font-size: 20px;
      color: #333333;
      border-top: 2px solid #000000;
      padding-top: 8px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="date-box">
      <div class="date">{date_str}</div>
      <div class="weekday">{weekday_str}</div>
    </div>
    <div class="weather">{weather_str}</div>
  </div>
  <div class="events">
    {items_html}
  </div>
  <div class="footer">
    更新于 {update_time} · 每15分钟自动刷新
  </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
