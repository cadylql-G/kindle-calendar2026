import html
import os
import urllib.request
from datetime import datetime
from icalendar import Calendar
import pytz

ics_url = os.environ["ICS_URL"]
tz_name = os.environ.get("TZ_NAME", "America/Toronto")
tz = pytz.timezone(tz_name)

now = datetime.now(tz)
today_str = now.strftime("%Y-%m-%d")
date_display = now.strftime("%Y年%m月%d日")
weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
weekday_display = weekday_map[now.weekday()]
updated_display = now.strftime("%H:%M")

req = urllib.request.Request(ics_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as resp:
    cal = Calendar.from_bytes(resp.read())

events = []
for component in cal.walk():
    if component.name == "VEVENT":
        dtstart = component.get("DTSTART").dt
        summary = str(component.get("SUMMARY", "无标题日程"))

        if hasattr(dtstart, "hour"):
            if dtstart.tzinfo is None:
                dt_local = tz.localize(dtstart)
            else:
                dt_local = dtstart.astimezone(tz)
            if dt_local.strftime("%Y-%m-%d") == today_str:
                events.append((dt_local.strftime("%H:%M"), summary, 0))
        else:
            if dtstart.strftime("%Y-%m-%d") == today_str:
                events.append(("全天", summary, 1))

events.sort(key=lambda x: (x[2], x[0]))

if events:
    rows_html = "\n".join(
        f'<div class="item"><span class="time">{html.escape(t)}</span> '
        f'<span class="title">{html.escape(s)}</span></div>'
        for t, s, _ in events
    )
else:
    rows_html = '<div class="empty">今天没有日程安排</div>'

page_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="900">
<title>今日日程</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 36px 40px;
    background: #FFFFFF;
    color: #000000;
    font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
  }}
  .header {{
    border-bottom: 4px solid #000000;
    padding-bottom: 22px;
    margin-bottom: 28px;
  }}
  .date {{
    font-size: 56px;
    font-weight: 700;
    line-height: 1.2;
  }}
  .weekday {{
    font-size: 38px;
    font-weight: 600;
    margin-top: 8px;
  }}
  .item {{
    border-bottom: 2px solid #CCCCCC;
    padding: 22px 0;
    font-size: 34px;
    line-height: 1.4;
  }}
  .time {{
    display: inline-block;
    min-width: 140px;
    font-weight: 700;
  }}
  .title {{
    font-weight: 500;
  }}
  .empty {{
    margin-top: 80px;
    text-align: center;
    font-size: 38px;
    color: #444444;
  }}
  .footer {{
    margin-top: 36px;
    font-size: 24px;
    color: #555555;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="date">{date_display}</div>
    <div class="weekday">{weekday_display}</div>
  </div>
  <div class="list">
    {rows_html}
  </div>
  <div class="footer">更新于 {updated_display} · 每15分钟自动刷新</div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(page_html)
