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
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


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
        start = 29 + 1.3 * bucket
        middle = start + 4
        end = start + 9
        return_start = 71 + .5 * bucket
        return_end = return_start + 4
        styles.append(f"""
      .b{bucket} {{ animation: dust{bucket} 20s ease-out infinite; }}
      .c{bucket} {{ animation: crumb{bucket} 20s ease-out infinite; }}
      @keyframes dust{bucket} {{
        0%, {start:.1f}% {{ opacity: 1; transform: none; }}
        {middle:.1f}% {{ opacity: .58; transform: translate(var(--mx), var(--my)) rotate(var(--rot)) scale(.72); }}
        {end:.1f}%, {return_start:.1f}% {{ opacity: 0; transform: translate(var(--dx), var(--dy)) rotate(var(--rot)) scale(.08); }}
        {return_end:.1f}%, 100% {{ opacity: 1; transform: none; }}
      }}
      @keyframes crumb{bucket} {{
        0%, {start:.1f}% {{ opacity: 0; transform: none; }}
        {start + 1:.1f}% {{ opacity: .85; transform: none; }}
        {end:.1f}%, 70% {{ opacity: 0; transform: translate(var(--dx), var(--dy)); }}
        {return_start + 1:.1f}% {{ opacity: .65; transform: translate(var(--dx), var(--dy)); }}
        {return_end:.1f}%, 100% {{ opacity: 0; transform: none; }}
      }}""")
    return "".join(styles)


def render_svg(weeks: list[dict], theme: str, glove_png_b64: str, red_glove_png_b64: str) -> str:
    if theme not in {"dark", "light"}:
        raise ValueError("theme must be dark or light")
    if not weeks or len(weeks) > 54:
        raise ValueError("contribution calendar must have 1 to 54 weeks")

    dark = theme == "dark"
    background = "#0d1117" if dark else "#ffffff"
    border = "#30363d" if dark else "#d0d7de"
    empty = "#151b23" if dark else "#ebedf0"
    colors = (
        (empty, "#033a16", "#196c2e", "#2ea043", "#56d364")
        if dark else (empty, "#9be9a8", "#40c463", "#30a14e", "#216e39")
    )
    label_color = "#e6edf3" if dark else "#24292f"
    muted_color = "#8b949e" if dark else "#57606a"
    cells, crumbs, month_labels = [], [], []
    last_month = None
    active_count = 0
    for week_index, week in enumerate(weeks):
        days = week["contributionDays"]
        if days:
            month = days[-1]["date"][5:7]
            if month != last_month:
                if month_labels and week_index - month_labels[-1][0] < 2:
                    month_labels.pop()
                month_labels.append((week_index, MONTHS[int(month) - 1]))
                last_month = month
        bucket = min(11, week_index * 12 // len(weeks))
        for day in days:
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
  <title id="title">Gold and red gauntlets snapping Kaveesha's GitHub contributions away and back</title>
  <desc id="description">The gold gauntlet turns {active_count} filled contribution squares and the rest of the grid to dust. After it leaves, the red gauntlet snaps the chart back into place. Red glove artwork adapted from the supplied Artwork_by_Goku image.</desc>
  <defs>
    <radialGradient id="aura"><stop stop-color="#fde047" stop-opacity=".85"/><stop offset=".45" stop-color="#a855f7" stop-opacity=".55"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>
    <radialGradient id="burst"><stop stop-color="#fff"/><stop offset=".2" stop-color="#fde047"/><stop offset="1" stop-color="#fbbf24" stop-opacity="0"/></radialGradient>
    <radialGradient id="red-aura"><stop stop-color="#fca5a5" stop-opacity=".9"/><stop offset=".45" stop-color="#ef4444" stop-opacity=".55"/><stop offset="1" stop-color="#991b1b" stop-opacity="0"/></radialGradient>
    <radialGradient id="red-burst"><stop stop-color="#fff"/><stop offset=".2" stop-color="#fecaca"/><stop offset="1" stop-color="#ef4444" stop-opacity="0"/></radialGradient>
    <image id="glove-art" x="448" y="52" width="64" height="85" href="data:image/png;base64,{glove_png_b64}"/>
    <image id="red-art" x="0" y="0" width="1024" height="1536" href="data:image/png;base64,{red_glove_png_b64}"/>
    <clipPath id="index-clip" clipPathUnits="userSpaceOnUse"><path d="M480 66 Q487 63 494 67 L502 71 L501 78 L493 81 L481 77Z"/></clipPath>
    <clipPath id="thumb-clip" clipPathUnits="userSpaceOnUse"><path d="M499 69 Q511 69 513 80 L512 94 L502 106 L492 103 L495 91 L493 78Z"/></clipPath>
    <mask id="base-mask" maskUnits="userSpaceOnUse" x="448" y="52" width="64" height="85"><rect x="448" y="52" width="64" height="85" fill="white"/><path d="M480 66 Q487 63 494 67 L502 71 L501 78 L493 81 L481 77Z" fill="black"/><path d="M499 69 Q511 69 513 80 L512 94 L502 106 L492 103 L495 91 L493 78Z" fill="black"/></mask>
    <linearGradient id="gold-wrist-fade" x1="0" y1="96" x2="0" y2="105" gradientUnits="userSpaceOnUse"><stop stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient>
    <mask id="gold-fade-mask" maskUnits="userSpaceOnUse" x="456" y="52" width="48" height="53"><rect x="456" y="52" width="48" height="53" fill="url(#gold-wrist-fade)"/></mask>
    <clipPath id="red-index-clip" clipPathUnits="userSpaceOnUse"><path d="M310 32 L425 20 L473 107 L485 345 L365 367 L345 265Z"/></clipPath>
    <clipPath id="red-thumb-clip" clipPathUnits="userSpaceOnUse"><path d="M145 350 L263 339 L378 445 L400 526 L303 622 L211 523Z"/></clipPath>
    <mask id="red-base-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="1024" height="1536"><rect width="1024" height="1536" fill="white"/><path d="M310 32 L425 20 L473 107 L485 345 L365 367 L345 265Z" fill="black"/><path d="M145 350 L263 339 L378 445 L400 526 L303 622 L211 523Z" fill="black"/></mask>
    <linearGradient id="red-wrist-fade" x1="0" y1="720" x2="0" y2="912" gradientUnits="userSpaceOnUse"><stop stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient>
    <mask id="red-fade-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="1024" height="912"><rect width="1024" height="912" fill="url(#red-wrist-fade)"/></mask>
  </defs>
  <style>
    .cell {{ transform-box: fill-box; transform-origin: center; }}
    .crumb {{ opacity: 0; }}
    .glow {{ transform-origin: 480px 95px; animation: gold-glow 20s ease-in-out infinite; }}
    .gauntlet {{ transform-origin: 500px 75px; animation: gold-snap 20s ease-in-out infinite; }}
    .index-finger {{ transform-origin: 483px 77px; animation: index-snap 20s ease-in-out infinite; }}
    .thumb {{ transform-origin: 499px 100px; animation: thumb-snap 20s ease-in-out infinite; }}
    .flash {{ transform-origin: 500px 75px; animation: gold-flash 20s ease-out infinite; }}
    .red-glow {{ transform-origin: 480px 95px; animation: red-glow 20s ease-in-out infinite; }}
    .red-gauntlet {{ transform-origin: 460px 78px; animation: red-snap 20s ease-in-out infinite; }}
    .red-index {{ transform-origin: 385px 350px; animation: red-index-snap 20s ease-in-out infinite; }}
    .red-thumb {{ transform-origin: 350px 535px; animation: red-thumb-snap 20s ease-in-out infinite; }}
    .red-flash {{ transform-origin: 460px 76px; animation: red-flash 20s ease-out infinite; }}
    {animation_styles()}
    @keyframes gold-glow {{
      0%, 14% {{ opacity: 0; transform: translateY(170px) scale(.65); }}
      22%, 27% {{ opacity: .85; transform: none; }}
      28% {{ opacity: 1; transform: scale(1.3); }}
      31%, 53% {{ opacity: .45; transform: none; }}
      60%, 100% {{ opacity: 0; transform: translateY(170px) scale(.8); }}
    }}
    @keyframes gold-snap {{
      0%, 14% {{ transform: translateY(170px); opacity: 0; }}
      22%, 27% {{ transform: none; opacity: 1; }}
      27.5% {{ transform: rotate(-2deg); }}
      28.5% {{ transform: rotate(2deg) scale(1.02); }}
      31%, 53% {{ transform: none; opacity: 1; }}
      60%, 100% {{ transform: translateY(170px); opacity: 0; }}
    }}
    @keyframes index-snap {{
      0%, 27% {{ transform: none; }}
      28% {{ transform: translate(2px, 3px) rotate(9deg); }}
      29% {{ transform: translate(-1px, 1px) rotate(-5deg); }}
      31%, 100% {{ transform: none; }}
    }}
    @keyframes thumb-snap {{
      0%, 27% {{ transform: none; }}
      28% {{ transform: translate(-2px, -2px) rotate(-9deg); }}
      29% {{ transform: translate(2px, 2px) rotate(8deg); }}
      31%, 100% {{ transform: none; }}
    }}
    @keyframes gold-flash {{
      0%, 27.5% {{ opacity: 0; transform: scale(.1); }}
      28.5% {{ opacity: 1; transform: scale(1.5); }}
      32%, 100% {{ opacity: 0; transform: scale(2.5); }}
    }}
    @keyframes red-glow {{
      0%, 60% {{ opacity: 0; transform: translateY(170px) scale(.65); }}
      67%, 69% {{ opacity: .85; transform: none; }}
      70% {{ opacity: 1; transform: scale(1.3); }}
      73%, 83% {{ opacity: .5; transform: none; }}
      90%, 100% {{ opacity: 0; transform: translateY(170px) scale(.8); }}
    }}
    @keyframes red-snap {{
      0%, 60% {{ opacity: 0; transform: translateY(170px); }}
      67%, 69% {{ opacity: 1; transform: none; }}
      69.5% {{ transform: rotate(-2deg); }}
      70.5% {{ transform: rotate(2deg) scale(1.02); }}
      73%, 83% {{ opacity: 1; transform: none; }}
      90%, 100% {{ opacity: 0; transform: translateY(170px); }}
    }}
    @keyframes red-index-snap {{
      0%, 68% {{ transform: none; }}
      70% {{ transform: rotate(-16deg); }}
      71% {{ transform: rotate(4deg); }}
      74%, 100% {{ transform: none; }}
    }}
    @keyframes red-thumb-snap {{
      0%, 68% {{ transform: none; }}
      70% {{ transform: rotate(20deg); }}
      71% {{ transform: rotate(-4deg); }}
      74%, 100% {{ transform: none; }}
    }}
    @keyframes red-flash {{
      0%, 69.5% {{ opacity: 0; transform: scale(.1); }}
      70.5% {{ opacity: 1; transform: scale(1.5); }}
      74%, 100% {{ opacity: 0; transform: scale(2.5); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .cell, .crumb, .glow, .gauntlet, .index-finger, .thumb, .flash, .red-glow, .red-gauntlet, .red-index, .red-thumb, .red-flash {{ animation: none; }}
      .cell {{ opacity: 1; transform: none; }}
      .crumb, .glow, .gauntlet, .flash, .red-glow, .red-gauntlet, .red-flash {{ opacity: 0; }}
    }}
  </style>
  <rect x=".5" y=".5" width="959" height="189" rx="16" fill="{background}" stroke="{border}"/>
  <g fill="{label_color}" font-family="Arial, sans-serif" font-size="11">{''.join(f'<text class="month-label" x="{30 + week_index * 17}" y="27">{month}</text>' for week_index, month in month_labels)}<text x="4" y="65">Mon</text><text x="4" y="99">Wed</text><text x="7" y="133">Fri</text></g>
  <g shape-rendering="geometricPrecision">{''.join(cells)}{''.join(crumbs)}</g>
  <g fill="{muted_color}" font-family="Arial, sans-serif" font-size="11"><text x="785" y="178">Less</text><text x="899" y="178">More</text></g>
  <g>{''.join(f'<rect class="legend-swatch" x="{814 + level * 17}" y="167" width="13" height="13" rx="2" fill="{color}"/>' for level, color in enumerate(colors))}</g>
  <circle class="glow" cx="480" cy="95" r="52" fill="url(#aura)"/>
  <g class="gauntlet"><svg x="435" y="40" width="90" height="108" viewBox="456 52 48 53" preserveAspectRatio="none" overflow="hidden"><g mask="url(#gold-fade-mask)"><use href="#glove-art" mask="url(#base-mask)"/><use class="index-finger" href="#glove-art" clip-path="url(#index-clip)"/><use class="thumb" href="#glove-art" clip-path="url(#thumb-clip)"/></g></svg></g>
  <g class="flash"><circle cx="500" cy="75" r="13" fill="url(#burst)"/><path d="M500 50v8 M500 92v8 M475 75h8 M517 75h8 M482 57l7 7 M511 86l7 7 M518 57l-7 7 M489 86l-7 7" stroke="#fde68a" stroke-width="2" stroke-linecap="round"/></g>
  <circle class="red-glow" cx="480" cy="95" r="52" fill="url(#red-aura)"/>
  <g class="red-gauntlet"><svg x="435" y="40" width="90" height="108" viewBox="130 0 760 912" overflow="hidden"><g mask="url(#red-fade-mask)"><use href="#red-art" mask="url(#red-base-mask)"/><use class="red-index" href="#red-art" clip-path="url(#red-index-clip)"/><use class="red-thumb" href="#red-art" clip-path="url(#red-thumb-clip)"/></g></svg></g>
  <g class="red-flash"><circle cx="460" cy="76" r="13" fill="url(#red-burst)"/><path d="M460 51v8 M460 93v8 M435 76h8 M477 76h8 M442 58l7 7 M471 87l7 7 M478 58l-7 7 M449 87l-7 7" stroke="#fecaca" stroke-width="2" stroke-linecap="round"/></g>
</svg>
'''


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not token or not username:
        raise SystemExit("GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER are required")
    glove = Path(__file__).resolve().parent.parent / "assets" / "snap-gauntlet.png"
    glove_png_b64 = base64.b64encode(glove.read_bytes()).decode("ascii")
    red_glove = Path(__file__).resolve().parent.parent / "assets" / "red-snap-gauntlet.png"
    red_glove_png_b64 = base64.b64encode(red_glove.read_bytes()).decode("ascii")
    weeks = fetch_weeks(username, token)
    output = Path("dist")
    output.mkdir(exist_ok=True)
    for theme, filename in (("light", "github-snap-calendar.svg"), ("dark", "github-snap-calendar-dark.svg")):
        (output / filename).write_text(render_svg(weeks, theme, glove_png_b64, red_glove_png_b64), encoding="utf-8")
    print(f"Generated snap animation from {len(weeks)} contribution weeks")


if __name__ == "__main__":
    main()
