"""Build a snap-and-dust animation from GitHub's contribution calendar."""

import base64
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
            "User-Agent": "github-profile-snap-generator",
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


def animation_styles() -> str:
    styles = []
    for bucket in range(12):
        start = 44 + 2 * bucket
        middle = start + 7
        end = start + 16
        styles.append(f"""
      .b{bucket} {{ animation: dust{bucket} 12s ease-out infinite; }}
      .c{bucket} {{ animation: crumb{bucket} 12s ease-out infinite; }}
      @keyframes dust{bucket} {{
        0% {{ opacity: 0; transform: none; }}
        8%, {start}% {{ opacity: 1; transform: none; }}
        {middle}% {{ opacity: .58; transform: translate(var(--mx), var(--my)) rotate(var(--rot)) scale(.72); }}
        {end}%, 95% {{ opacity: 0; transform: translate(var(--dx), var(--dy)) rotate(var(--rot)) scale(.08); }}
        99%, 100% {{ opacity: 0; transform: none; }}
      }}
      @keyframes crumb{bucket} {{
        0%, {start}% {{ opacity: 0; transform: none; }}
        {start + 2}% {{ opacity: .85; transform: none; }}
        {end}%, 100% {{ opacity: 0; transform: translate(var(--dx), var(--dy)); }}
      }}""")
    return "".join(styles)


def render_svg(weeks: list[dict], theme: str, glove_png_b64: str) -> str:
    if theme not in {"dark", "light"}:
        raise ValueError("theme must be dark or light")
    if not weeks or len(weeks) > 54:
        raise ValueError("contribution calendar must have 1 to 54 weeks")

    dark = theme == "dark"
    background = "#0d1117" if dark else "#ffffff"
    border = "#30363d" if dark else "#d0d7de"
    empty = "#1b232c" if dark else "#ebedf0"
    colors = (
        (empty, "#0e665d", "#088b7b", "#0fb69a", "#39ddb1")
        if dark else (empty, "#b9e9dd", "#77d9bd", "#34bb98", "#128a72")
    )
    cells, crumbs = [], []
    active_count = 0
    for week_index, week in enumerate(weeks):
        bucket = min(11, week_index * 12 // len(weeks))
        for day in week["contributionDays"]:
            weekday = day["weekday"]
            level = LEVELS[day["contributionLevel"]]
            count = day["contributionCount"]
            if not 0 <= weekday <= 6 or not isinstance(count, int) or count < 0:
                raise ValueError("invalid contribution day")
            active_count += level > 0
            x, y = 30 + week_index * 17, 37 + weekday * 17
            drift_x = 28 + (week_index * 13 + weekday * 7) % 60
            drift_y = -18 - (week_index * 5 + weekday * 11) % 45
            rotation = 20 + (week_index * 9 + weekday * 17) % 70
            style = (
                f"--mx:{drift_x // 3}px;--my:{drift_y // 3}px;"
                f"--dx:{drift_x}px;--dy:{drift_y}px;--rot:{rotation}deg"
            )
            date = html.escape(day["date"])
            title = f"{date}: {count} contribution{'s' if count != 1 else ''}"
            cells.append(
                f'<rect class="cell b{bucket}" x="{x}" y="{y}" width="15" height="15" '
                f'rx="2" fill="{colors[level]}" style="{style}"><title>{title}</title></rect>'
            )
            for fragment in range(3 if level else 1):
                jitter_x = (week_index * 7 + weekday * 3 + fragment * 4) % 8
                jitter_y = (week_index * 3 + weekday * 5 + fragment * 6) % 8
                crumbs.append(
                    f'<circle class="crumb c{bucket}" cx="{x + 2 + jitter_x}" cy="{y + 2 + jitter_y}" '
                    f'r="{1.1 + fragment * .35:.2f}" fill="{colors[level]}" '
                    f'style="--dx:{drift_x + fragment * 13}px;--dy:{drift_y - fragment * 9}px"/>'
                )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="190" viewBox="0 0 960 190" role="img" aria-labelledby="title description">
  <title id="title">Golden gauntlet snapping Kaveesha's GitHub contributions into dust</title>
  <desc id="description">The full contribution calendar glows, then {active_count} filled squares and the rest of the grid drift away as dust after a snap.</desc>
  <defs>
    <radialGradient id="aura"><stop stop-color="#fde047" stop-opacity=".85"/><stop offset=".45" stop-color="#a855f7" stop-opacity=".55"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>
    <radialGradient id="burst"><stop stop-color="#fff"/><stop offset=".2" stop-color="#fde047"/><stop offset="1" stop-color="#fbbf24" stop-opacity="0"/></radialGradient>
    <image id="glove-art" x="448" y="52" width="64" height="85" href="data:image/png;base64,{glove_png_b64}"/>
    <clipPath id="index-clip" clipPathUnits="userSpaceOnUse"><path d="M480 66 Q487 63 494 67 L502 71 L501 78 L493 81 L481 77Z"/></clipPath>
    <clipPath id="thumb-clip" clipPathUnits="userSpaceOnUse"><path d="M499 69 Q511 69 513 80 L512 94 L502 106 L492 103 L495 91 L493 78Z"/></clipPath>
    <mask id="base-mask" maskUnits="userSpaceOnUse" x="448" y="52" width="64" height="85"><rect x="448" y="52" width="64" height="85" fill="white"/><path d="M480 66 Q487 63 494 67 L502 71 L501 78 L493 81 L481 77Z" fill="black"/><path d="M499 69 Q511 69 513 80 L512 94 L502 106 L492 103 L495 91 L493 78Z" fill="black"/></mask>
  </defs>
  <style>
    .cell {{ transform-box: fill-box; transform-origin: center; }}
    .crumb {{ opacity: 0; }}
    .glow {{ transform-origin: 480px 95px; animation: glow 12s ease-in-out infinite; }}
    .gauntlet {{ transform-origin: 500px 75px; animation: snap 12s ease-in-out infinite; }}
    .index-finger {{ transform-origin: 483px 77px; animation: index-snap 12s ease-in-out infinite; }}
    .thumb {{ transform-origin: 499px 100px; animation: thumb-snap 12s ease-in-out infinite; }}
    .flash {{ transform-origin: 500px 75px; animation: flash 12s ease-out infinite; }}
    {animation_styles()}
    @keyframes glow {{
      0%, 24% {{ opacity: 0; transform: translateY(170px) scale(.65); }}
      28% {{ opacity: 0; transform: translateY(0) scale(.65); }}
      34%, 38% {{ opacity: .85; transform: translateY(0) scale(1); }}
      41% {{ opacity: 1; transform: translateY(0) scale(1.3); }}
      50%, 82% {{ opacity: .45; transform: translateY(0) scale(1); }}
      94%, 100% {{ opacity: 0; transform: translateY(170px) scale(.8); }}
    }}
    @keyframes snap {{
      0%, 12% {{ transform: translateY(170px); opacity: 0; }}
      29%, 38% {{ transform: translateY(0); opacity: 1; }}
      39.5% {{ transform: rotate(-2deg); }}
      41% {{ transform: rotate(2deg) scale(1.02); }}
      43%, 84% {{ transform: rotate(0deg); opacity: 1; }}
      94%, 100% {{ transform: translateY(170px); opacity: 0; }}
    }}
    @keyframes index-snap {{
      0%, 38% {{ transform: none; }}
      40.5% {{ transform: translate(2px, 3px) rotate(9deg); }}
      41.5% {{ transform: translate(-1px, 1px) rotate(-5deg); }}
      44%, 100% {{ transform: none; }}
    }}
    @keyframes thumb-snap {{
      0%, 38% {{ transform: none; }}
      40.5% {{ transform: translate(-2px, -2px) rotate(-9deg); }}
      41.5% {{ transform: translate(2px, 2px) rotate(8deg); }}
      44%, 100% {{ transform: none; }}
    }}
    @keyframes flash {{
      0%, 39.5% {{ opacity: 0; transform: scale(.1); }}
      41% {{ opacity: 1; transform: scale(1.5); }}
      45%, 100% {{ opacity: 0; transform: scale(2.5); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .cell, .crumb, .glow, .gauntlet, .index-finger, .thumb, .flash {{ animation: none; }}
      .cell {{ opacity: 1; transform: none; }}
      .crumb, .glow, .flash {{ opacity: 0; }}
    }}
  </style>
  <rect x=".5" y=".5" width="959" height="189" rx="16" fill="{background}" stroke="{border}"/>
  <g shape-rendering="geometricPrecision">{''.join(cells)}{''.join(crumbs)}</g>
  <circle class="glow" cx="480" cy="95" r="52" fill="url(#aura)"/>
  <g class="gauntlet"><use href="#glove-art" mask="url(#base-mask)"/><use class="index-finger" href="#glove-art" clip-path="url(#index-clip)"/><use class="thumb" href="#glove-art" clip-path="url(#thumb-clip)"/></g>
  <g class="flash"><circle cx="500" cy="75" r="13" fill="url(#burst)"/><path d="M500 50v8 M500 92v8 M475 75h8 M517 75h8 M482 57l7 7 M511 86l7 7 M518 57l-7 7 M489 86l-7 7" stroke="#fde68a" stroke-width="2" stroke-linecap="round"/></g>
</svg>
'''


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not token or not username:
        raise SystemExit("GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER are required")
    glove = Path(__file__).resolve().parent.parent / "assets" / "snap-gauntlet.png"
    glove_png_b64 = base64.b64encode(glove.read_bytes()).decode("ascii")
    weeks = fetch_weeks(username, token)
    output = Path("dist")
    output.mkdir(exist_ok=True)
    for theme, filename in (("light", "github-snap-fingers.svg"), ("dark", "github-snap-fingers-dark.svg")):
        (output / filename).write_text(render_svg(weeks, theme, glove_png_b64), encoding="utf-8")
    print(f"Generated snap animation from {len(weeks)} contribution weeks")


if __name__ == "__main__":
    main()
