"""
Scrapes https://www.parkenstadion.dk/kalender and writes an updated
docs/parken-kalender.ics file. Designed to be run daily by a GitHub Action.

If Parken redesigns their site, the event link pattern (/begivenheder/)
is the most stable anchor to search from, so that's what this looks for.
"""
import re
from datetime import datetime, timedelta

import pytz
import requests
from bs4 import BeautifulSoup

URL = "https://www.parkenstadion.dk/kalender"
TZ = pytz.timezone("Europe/Copenhagen")
DEFAULT_DURATION_HOURS = 2  # site doesn't list end times, so we assume 2 hours
OUTPUT_PATH = "docs/parken-kalender.ics"

DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})")


def fetch_events():
    resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    seen_hrefs = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/begivenheder/" not in href or href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        # Walk up the DOM until we find both a heading (title) and a date
        # nearby. This tolerates markup changes better than fixed CSS classes.
        title = None
        date_match = None
        container = a
        for _ in range(6):
            if container.parent is None:
                break
            container = container.parent
            text = container.get_text(" ", strip=True)
            if date_match is None:
                date_match = DATE_RE.search(text)
            if title is None:
                heading = container.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                if heading:
                    title = heading.get_text(strip=True)
            if title and date_match:
                break

        if not (title and date_match):
            continue

        day, month, year, hour, minute = (int(x) for x in date_match.groups())
        start = TZ.localize(datetime(year, month, day, hour, minute))
        end = start + timedelta(hours=DEFAULT_DURATION_HOURS)
        full_url = href if href.startswith("http") else f"https://www.parkenstadion.dk{href}"

        events.append({"title": title, "start": start, "end": end, "url": full_url})

    events.sort(key=lambda e: e["start"])
    return events


def escape_ics_text(text):
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def build_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Parken Stadion Kalender//EN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Parken Stadion",
        "X-WR-TIMEZONE:Europe/Copenhagen",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for i, ev in enumerate(events, start=1):
        uid = f"{i}-{ev['start'].strftime('%Y%m%d%H%M')}@parkenstadion.dk"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;TZID=Europe/Copenhagen:{ev['start'].strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID=Europe/Copenhagen:{ev['end'].strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{escape_ics_text(ev['title'])}",
            "LOCATION:Parken Stadion\\, Per Henrik Lings Allé 2\\, 2100 København Ø",
            f"URL:{ev['url']}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main():
    events = fetch_events()
    ics_content = build_ics(events)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(ics_content)
    print(f"Wrote {len(events)} events to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
