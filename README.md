# Trentino Events

Event portal for Rovereto, Vallagarina, Trento, Alto Garda and the rest of Trentino.

## Current front-end basics
- German / English / Italian switch
- Responsive compact visual event cards with imagery
- Localized change badges (NEW/NEU/NUOVO, UPDATED/AKTUALISIERT/AGGIORNATO, etc.)
- No permanent “new” badge on baseline events
- Dynamic today date using Europe/Rome
- Quick date filters, area/category filters and search
- Event detail dialog with image and official source link
- Event data isolated in `data/events.json`
- Exclusions isolated in `data/exclusions.json`

## Coverage architecture
The event research process is **enumeration-first**, not search-result-first.

`data/source_registry.json` contains the persistent source inventory and source-specific scan contract. Known event calendars must be traversed exhaustively: all pagination/load-more pages, date buckets, category tabs, child event pages, recurring/“other dates” entries and linked PDFs/brochures/flyers.

`data/source_audit.json` records whether each required source was completely scanned. When a source exposes a total result count, the number of unique records seen must be reconciled with that count before the source can be marked `COMPLETE`. A timeout, blocked attachment, broken pagination or count mismatch must be recorded as `PARTIAL` or `FAILED` rather than silently ignored.

Search engines are used to **discover additional sources**, not as proof that a known event calendar has been fully scanned.

Coverage includes, where publicly accessible:
- regional and municipal event calendars
- tourism boards and territorial APT/DMO calendars
- Trentino Cultura, museums, theatres, libraries and venues
- festival, sports, trade-fair and organizer websites
- Pro Loco and local association calendars
- wine, agriculture and gastronomy organizations
- public Facebook/Instagram/other social announcements
- public flyers, downloadable PDFs and programme brochures
- local-media event roundups as discovery/corroboration sources

New recurring sources discovered during research should be added to `data/source_registry.json` so the source universe grows over time instead of being rediscovered ad hoc.

## Daily data updates
The recurring daily process maintains a rolling 12-month window. It should update:
- `data/events.json`
- `data/source_audit.json`
- `data/source_registry.json` when a durable new source is discovered
- `data/exclusions.json` when exclusions change

Frontend files should remain untouched during routine data updates.

For each event retain name, dates, time, municipality, area, venue, category, short descriptions in German/English/Italian, organizer, price, official/public URL, source, confirmation state, verification date and event image when reliably available. Optional recurrence/occurrence/source-confidence metadata may be stored for recurring or social/flyer-discovered events.

New/updated/cancelled/confirmed/removed events may carry a transient `status` and `statusDate`; unchanged events must not be labelled as new. Status badges expire after 7 days for normal still-active events.

If any mandatory P0 source cannot be fully scanned, the run must explicitly surface a **coverage warning**. A partial scan must never be presented as a complete “no changes” result.
