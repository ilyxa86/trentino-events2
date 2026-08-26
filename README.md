# Trentino Events

Bilingual event portal for Rovereto, Vallagarina, Trento, Alto Garda and the rest of Trentino.

## Current front-end basics
- English / Italian switch
- Responsive visual event cards with imagery
- Localized change badges (NEW/NUOVO, UPDATED/AGGIORNATO, etc.)
- No permanent “new” badge on baseline events
- Dynamic today date using Europe/Rome
- Quick date filters, area/category filters and search
- Event detail dialog with image and official source link
- Event data isolated in `data/events.json`
- Exclusions isolated in `data/exclusions.json`

## Daily data updates
Routine daily automation should update `data/events.json` only and preserve the front-end files. New/updated/cancelled/confirmed/removed events may carry a transient `status` and `changeDate`; unchanged events should not be labelled as new.


## Visual redesign
- Large photographic event cards
- Official event image supported via `image` in `data/events.json`
- Automatic thematic fallback photography if no official image exists
- Bilingual change badges (`New/Nuovo`, `Updated/Aggiornato`, etc.)
- Change badges expire visually after 7 days when `statusDate` is present
- Clickable category chips
- Visible daily-update indicator (07:00 Europe/Rome)

The recurring event-research process should update only `data/events.json` and `data/exclusions.json`; the frontend design should remain untouched during routine updates.
