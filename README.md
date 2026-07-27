[README.md](https://github.com/user-attachments/files/30402172/README.md)
# parken-calendar# parken-calendar

Scrapes the events listed on [Parken Stadion's calendar page](https://www.parkenstadion.dk/kalender)
once a day and republishes them as a subscribable `.ics` calendar feed —
so matches, concerts, and other events at Parken show up automatically in
your phone's calendar app without you ever visiting the site.

## How it works

1. `scrape_parken.py` fetches the Parken calendar page and pulls out each
   event's title, date/time, and link (matched via the stable
   `/begivenheder/` URL pattern, so it should survive minor site redesigns).
2. A [GitHub Actions workflow](.github/workflows/update-calendar.yml) runs
   that script every day and commits the result to
   [`docs/parken-kalender.ics`](docs/parken-kalender.ics).
3. GitHub Pages serves that file at a stable URL, which any calendar app
   can subscribe to.

Event durations default to 2 hours, since Parken's page only lists start
times.

## Subscribe to the calendar

Add this feed to your calendar app:

```
webcal://anderssvante.github.io/parken-calendar/parken-kalender.ics
```

- **iPhone / Apple Calendar**: open that link directly (e.g. paste into
  Safari), or go to Settings → Calendar → Accounts → Add Account → Other →
  Add Subscribed Calendar and paste the `https://` version instead:
  `https://anderssvante.github.io/parken-calendar/parken-kalender.ics`
- **Google Calendar**: the mobile app doesn't support subscribing to a URL
  directly — on a desktop browser, go to Google Calendar → Other calendars
  (+) → "From URL" and paste the `https://` link above. It'll then appear
  in the Google Calendar app on your phone as well.

Calendar apps typically re-check subscribed feeds roughly once every 24
hours, so new or changed events show up automatically within a day of the
site updating — no manual re-import needed.

## Running it yourself

```bash
pip install requests beautifulsoup4 pytz
python scrape_parken.py
```

This writes/updates `docs/parken-kalender.ics` locally.

## Repo layout

| Path | Purpose |
|---|---|
| `scrape_parken.py` | Scrapes the site and generates the `.ics` file |
| `.github/workflows/update-calendar.yml` | Runs the scraper daily via GitHub Actions and commits changes |
| `docs/parken-kalender.ics` | The generated calendar feed, served via GitHub Pages |

## Maintenance notes

- If Parken redesigns their site and the scraper stops finding events,
  start by checking whether event links still contain `/begivenheder/` —
  that's the anchor `fetch_events()` in `scrape_parken.py` searches for.
- The daily schedule is set via the `cron` line in
  `.github/workflows/update-calendar.yml` (currently 05:00 UTC / ~07:00
  Copenhagen time).
