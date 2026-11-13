import calendar
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
import sys


class ContributionCalendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.summary = ""
        self.in_summary = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "h2" and attrs.get("id") == "js-contribution-activity-description":
            self.in_summary = True
        if tag == "td" and "ContributionCalendar-day" in attrs.get("class", "").split():
            day = date.fromisoformat(attrs["data-date"])
            level = int(attrs["data-level"])
            if day in self.days or not 0 <= level <= 4:
                raise ValueError("Unexpected GitHub contribution cell")
            self.days[day] = level

    def handle_endtag(self, tag):
        if tag == "h2":
            self.in_summary = False

    def handle_data(self, text):
        if self.in_summary:
            self.summary += text


chart = ContributionCalendar()
chart.feed(sys.stdin.read())
summary = " ".join(chart.summary.split())
if not 360 <= len(chart.days) <= 371 or not summary.endswith("in the last year"):
    raise ValueError("Expected GitHub's public rolling contribution calendar")

first, last = min(chart.days), max(chart.days)
if (last - first).days + 1 != len(chart.days):
    raise ValueError("GitHub's contribution calendar is missing dates")

palette = ("#24473e", "#588866", "#b68339", "#e6b34d", "#ffe0a0")
start = first - timedelta(days=(first.weekday() + 1) % 7)
weeks = (last - start).days // 7 + 1
step = 17
left = (960 - weeks * step + 3) // 2
labels, cells = [], []
for day, level in sorted(chart.days.items()):
    week, row = divmod((day - start).days, 7)
    x, y = left + week * step, 75 + row * step
    if day == first or day.day == 1:
        labels.append(f'<text x="{x}" y="65">{calendar.month_abbr[day.month]}</text>')
    cells.append(f'<rect x="{x}" y="{y}" width="14" height="14" rx="3" fill="{palette[level]}"/>')

legend = "\n".join(
    f'<rect x="{776 + index * step}" y="207" width="14" height="14" rx="3" fill="{color}"/>'
    for index, color in enumerate(palette)
)
total = summary.split()[0]
if not total.replace(",", "").isdecimal():
    raise ValueError("Expected a numeric contribution count")
count_label = "contribution" if total == "1" else "contributions"

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="242" viewBox="0 0 960 242" role="img" aria-labelledby="title">
  <title id="title">{total} {count_label} in the last year for NnaroTaruo</title>
  <style>
    .swell {{ animation: roll 7s linear infinite; }}
    @keyframes roll {{
      0%, 15% {{ transform: translateX(-160px); }}
      85%, 100% {{ transform: translateX(960px); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .swell {{ display: none; }} }}
  </style>
  <defs>
    <linearGradient id="wash">
      <stop stop-color="#142e28"/>
      <stop offset="1" stop-color="#193b32"/>
    </linearGradient>
    <linearGradient id="foam">
      <stop stop-color="#ffe0a0" stop-opacity="0"/>
      <stop offset=".7" stop-color="#ffe0a0" stop-opacity=".22"/>
      <stop offset="1" stop-color="#ffe0a0" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="grid"><rect x="{left}" y="75" width="{weeks * step - 3}" height="116"/></clipPath>
  </defs>
  <rect width="960" height="242" rx="12" fill="url(#wash)"/>
  <circle cx="{left + 7}" cy="31" r="7" fill="#e6b34d"/>
  <text x="{left + 24}" y="37" fill="#ffe6b5" font-family="system-ui, sans-serif" font-size="19" font-weight="650">{total} {count_label} in the last year</text>
  <g fill="#ead5ac" font-family="system-ui, sans-serif" font-size="13">
    {chr(10).join(labels)}
    <text x="740" y="218">Less</text>
    <text x="866" y="218">More</text>
  </g>
  <g fill="#ead5ac" font-family="system-ui, sans-serif" font-size="9" text-anchor="end">
    <text x="{left - 4}" y="102">Mon</text>
    <text x="{left - 4}" y="136">Wed</text>
    <text x="{left - 4}" y="170">Fri</text>
  </g>
  {chr(10).join(cells)}
  {legend}
  <g clip-path="url(#grid)">
    <path class="swell" d="M0 192Q35 152 30 114T65 69h87Q102 93 108 120T80 192Z" fill="url(#foam)"/>
  </g>
</svg>
"""

Path("assets/nnarotaruo-contributions.svg").write_bytes(svg.encode("utf-8"))
