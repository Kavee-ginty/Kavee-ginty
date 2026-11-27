"""Build animated contribution-grid SVGs from GitHub's contribution calendar."""

import html
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays { date weekday contributionCount contributionLevel }
        }
      }
    }
  }
}"""

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_weeks(username: str, token: str) -> list[dict]:
    payload = json.dumps({"query": QUERY, "variables": {"login": username}}).encode()
    request = Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "github-profile-bending-generator",
        },
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise ValueError(f"GitHub GraphQL error: {result['errors'][0]['message']}")
    try:
        weeks = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except (KeyError, TypeError) as exc:
        raise ValueError("GitHub did not return a contribution calendar") from exc
    if not weeks:
        raise ValueError("GitHub returned an empty contribution calendar")
    return weeks


def render_svg(weeks: list[dict], theme: str) -> str:
    if theme not in {"dark", "light"}:
        raise ValueError("theme must be dark or light")
    if len(weeks) > 54:
        raise ValueError("contribution calendar has too many weeks")

    dark = theme == "dark"
    background = "#0d1117" if dark else "#ffffff"
    border = "#30363d" if dark else "#d0d7de"
    empty = "#1b232c" if dark else "#ebedf0"
    colors = (
        (empty, "#0e665d", "#088b7b", "#0fb69a", "#39ddb1")
        if dark else (empty, "#b9e9dd", "#77d9bd", "#34bb98", "#128a72")
    )
    air = "#67e8f9" if dark else "#0e7490"
    cells = []
    active_count = 0
    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            weekday = day["weekday"]
            level = LEVELS[day["contributionLevel"]]
            count = day["contributionCount"]
            if not 0 <= weekday <= 6 or not isinstance(count, int) or count < 0:
                raise ValueError("invalid contribution day")
            x, y = 300 + week_index * 15, 76 + weekday * 15
            date = html.escape(day["date"])
            title = f"{date}: {count} contribution{'s' if count != 1 else ''}"
            if level:
                active_count += 1
                delay = 0.25 + week_index * 0.055 + weekday * 0.075
                attrs = (
                    f' class="active" style="--dx:{215 - x}px;--dy:{142 - y}px;'
                    f'animation-delay:-{delay + 2:.3f}s"'
                )
            else:
                attrs = ""
            cells.append(
                f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" '
                f'fill="{colors[level]}"{attrs}><title>{title}</title></rect>'
            )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="260" viewBox="0 0 1160 260" role="img" aria-labelledby="title description">
  <title id="title">Aang bending Kaveesha's GitHub contributions into place</title>
  <desc id="description">An animated airbender sends {active_count} filled contribution squares into a calendar grid.</desc>
  <defs>
    <linearGradient id="air" x1="0" y1="1" x2="1" y2="0">
      <stop stop-color="#8b5cf6"/><stop offset="0.55" stop-color="{air}"/><stop offset="1" stop-color="#34d399"/>
    </linearGradient>
  </defs>
  <style>
    .active {{ transform-box: fill-box; transform-origin: center; animation: arrive 12s cubic-bezier(.2,.7,.2,1) infinite both; }}
    .bender {{ animation: breathe 3s ease-in-out infinite; }}
    .air {{ fill: none; stroke: url(#air); stroke-linecap: round; stroke-dasharray: 8 12; animation: flow 2s linear infinite; }}
    @keyframes arrive {{
      0%, 4% {{ transform: translate(var(--dx), var(--dy)) scale(.2) rotate(-30deg); opacity: 0; }}
      18% {{ opacity: 1; }}
      34%, 86% {{ transform: translate(0, 0) scale(1) rotate(0); opacity: 1; }}
      96%, 100% {{ transform: translate(0, 0) scale(1); opacity: 0; }}
    }}
    @keyframes flow {{ to {{ stroke-dashoffset: -40; }} }}
    @keyframes breathe {{ 50% {{ transform: translateY(-4px); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .active, .bender, .air {{ animation: none; }}
      .active {{ opacity: 1; }}
    }}
  </style>
  <rect x="0.5" y="0.5" width="1159" height="259" rx="18" fill="{background}" stroke="{border}"/>
  <path class="air" stroke-width="5" d="M198 126 C238 77 287 84 305 109 S265 166 227 145 C193 127 236 95 259 112 C294 139 322 123 341 100"/>
  <path class="air" stroke-width="2.5" opacity=".65" d="M191 163 C233 205 288 189 299 158 S255 123 244 151 C235 171 272 176 295 163"/>
  <g class="bender">
    <ellipse cx="116" cy="225" rx="68" ry="9" fill="{border}" opacity=".5"/>
    <!-- Robes and stance -->
    <path d="M94 174 L73 220 L105 222 L124 186 L143 222 L174 219 L145 170Z" fill="#a24819" stroke="#4b281b" stroke-width="3"/>
    <path d="M87 202 L76 222 L108 224 L119 199 M139 199 L154 224 L178 221 L158 194" fill="#d8922f" stroke="#4b281b" stroke-width="3"/>
    <path d="M78 119 Q118 98 160 124 L151 185 Q120 206 82 181Z" fill="#e9a538" stroke="#5b3222" stroke-width="3"/>
    <path d="M96 115 Q124 133 148 119 L137 184 Q114 192 93 181Z" fill="#f8cf69"/>
    <path d="M83 168 Q118 180 154 168 L151 181 Q118 191 82 181Z" fill="#b34f26"/>
    <!-- Outstretched bending arms -->
    <path d="M84 127 Q66 140 54 155 L67 165 L95 149 M155 126 Q179 133 194 124 L201 139 Q184 155 155 150" fill="#e9a538" stroke="#5b3222" stroke-width="3"/>
    <path d="M55 153 Q45 151 41 160 Q46 171 62 169 L69 162 M194 125 Q208 112 219 116 Q224 123 217 131 L201 140" fill="#f3c796" stroke="#7d4b32" stroke-width="3"/>
    <!-- Head, ears, and the blue airbender arrow -->
    <ellipse cx="119" cy="71" rx="39" ry="45" fill="#f3c796" stroke="#7d4b32" stroke-width="3"/>
    <ellipse cx="80" cy="78" rx="7" ry="12" fill="#f3c796" stroke="#7d4b32" stroke-width="2"/>
    <ellipse cx="158" cy="78" rx="7" ry="12" fill="#f3c796" stroke="#7d4b32" stroke-width="2"/>
    <path d="M119 26 L109 61 L116 59 L119 74 L122 59 L129 61Z" fill="#6ed8ec" stroke="#167b9f" stroke-width="2"/>
    <path d="M98 80 Q105 75 112 80 M127 80 Q135 75 142 80" fill="none" stroke="#43342d" stroke-width="3" stroke-linecap="round"/>
    <path d="M113 99 Q120 105 128 99" fill="none" stroke="#9d5f48" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M112 113 L119 130 L127 113" fill="#f3c796"/>
  </g>
  <g shape-rendering="geometricPrecision">{''.join(cells)}</g>
</svg>
'''


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not token or not username:
        raise SystemExit("GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER are required")
    weeks = fetch_weeks(username, token)
    output = Path("dist")
    output.mkdir(exist_ok=True)
    for theme, filename in (("light", "github-bending.svg"), ("dark", "github-bending-dark.svg")):
        (output / filename).write_text(render_svg(weeks, theme), encoding="utf-8")
    print(f"Generated bending animation from {len(weeks)} contribution weeks")


if __name__ == "__main__":
    main()
