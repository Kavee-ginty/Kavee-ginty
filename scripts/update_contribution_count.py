"""Keep the README heading in sync with GitHub's visible contribution graph."""

import os
import re
import time
from html import unescape
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


HEADING = re.compile(r"(?m)^## [\d,]+ contributions? in the last year(?=\r?$)")


def parse_count(page: str) -> int:
    match = re.search(
        r'<h2\b[^>]*\bid="js-contribution-activity-description"[^>]*>(.*?)</h2>',
        page,
        re.DOTALL,
    )
    if not match:
        raise ValueError("GitHub contribution heading was not found")
    label = " ".join(re.sub(r"<[^>]*>", " ", unescape(match.group(1))).split())
    count = re.fullmatch(r"([\d,]+) contributions? in the last year", label)
    if not count:
        raise ValueError(f"Unexpected GitHub contribution heading: {label}")
    return int(count.group(1).replace(",", ""))


def fetch_count(username: str) -> int:
    url = f"https://github.com/users/{quote(username, safe='')}/contributions"
    request = Request(url, headers={"User-Agent": "Kavee-ginty-profile-updater"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                return parse_count(response.read().decode("utf-8"))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Unreachable")


def replace_heading(readme: str, count: int) -> str:
    label = "contribution" if count == 1 else "contributions"
    updated, matches = HEADING.subn(f"## {count:,} {label} in the last year", readme)
    if matches != 1:
        raise ValueError(f"Expected one contribution heading, found {matches}")
    return updated


def main() -> None:
    username = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not username:
        raise SystemExit("GITHUB_REPOSITORY_OWNER is required")
    count = fetch_count(username)
    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    original = readme_path.read_bytes().decode("utf-8")
    updated = replace_heading(original, count)
    if updated != original:
        readme_path.write_bytes(updated.encode("utf-8"))
    print(f"Yearly contribution heading: {count:,}")


if __name__ == "__main__":
    main()
