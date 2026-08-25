# Trentino Events website

A bilingual (English / Italian) event browser for Rovereto, Vallagarina, Trento, Alto Garda and the rest of Trentino.

## Included
- English / Italian language switch
- Clickable quick date ranges: Today, This week, Weekend, This month, Next 12 months
- Custom From / To date fields
- Area, category and free-text filters
- Event detail modal
- Status badges: NEW / UPDATED / CONFIRMED / Not yet confirmed
- Official event links and verification date
- Responsive phone / tablet / desktop layout
- Event data stored separately in `data/events.json`
- Permanent exclusions stored in `data/exclusions.json`

## Local preview
Because the app loads `data/events.json`, serve the directory instead of double-clicking `index.html`.

Python:
    python -m http.server 8000

Then open:
    http://localhost:8000

## Updating the website
The front end does not need to change. Replace or modify `data/events.json` each morning.

Recommended production architecture:
1. Host the repository on GitHub.
2. Deploy it on Vercel (or GitHub Pages).
3. Let the daily ChatGPT event-monitoring workflow update `data/events.json`.
4. The hosting platform redeploys automatically whenever the JSON changes.

## Important
The current prototype uses 2026-08-25 as its baseline date so its quick date controls match the requested monitoring window. In production, the update process should write the current run date into the generated dataset or configuration each morning.
