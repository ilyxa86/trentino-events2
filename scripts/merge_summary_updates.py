"""Merge a finished summary pass into the latest event snapshot by event ID.

Only summary fields and repaired non-detail links can change. Newer curated
descriptions, dates, status, locations and unrelated source updates win.
"""
import json
import sys
from pathlib import Path

from event_descriptions import substantive, event_detail_url


def merge_summaries(base, generated, latest):
    old_by_id = {e["id"]: e for e in base}
    new_by_id = {e["id"]: e for e in generated}
    for event in latest:
        old, new = old_by_id.get(event["id"]), new_by_id.get(event["id"])
        if old is None or new is None:
            continue
        if any(event.get(k) != old.get(k) for k in ("name", "startDate", "endDate")):
            continue
        if any(substantive(text) and substantive((event.get("description") or {}).get(lang))
               and text != event["description"][lang]
               for lang, text in (old.get("description") or {}).items()):
            continue  # Source copy changed while research was in flight.
        descriptions = dict(event.get("description") or {})
        sources = dict(event.get("descriptionSources") or {})
        changed = False
        for lang in ("de", "en", "it"):
            before = (old.get("description") or {}).get(lang)
            after = (new.get("description") or {}).get(lang)
            current = descriptions.get(lang)
            if after == before or (current != before and substantive(current)):
                continue
            if substantive(after):
                descriptions[lang] = after
                source = (new.get("descriptionSources") or {}).get(lang)
                if source:
                    sources[lang] = source
                changed = True
            elif current == before and (event.get("descriptionSources") or {}).get(lang) and not event_detail_url(event["descriptionSources"][lang]):
                descriptions.pop(lang, None)
                sources.pop(lang, None)
                changed = True
        if changed:
            event["description"] = descriptions
            event["descriptionSources"] = sources
            event["descriptionStatus"] = "complete" if all(substantive(descriptions.get(l)) for l in ("de", "en", "it")) else "partial" if any(substantive(v) for v in descriptions.values()) else "missing"
            event["descriptionVerified"] = new.get("descriptionVerified")
        current_url = event.get("officialUrl")
        new_url = new.get("officialUrl")
        if current_url == old.get("officialUrl") and not event_detail_url(current_url) and event_detail_url(new_url):
            event["officialUrl"] = new_url
    return latest


def main():
    base, generated, latest = [json.loads(Path(p).read_text(encoding="utf-8-sig")) for p in sys.argv[1:4]]
    Path(sys.argv[3]).write_text(json.dumps(merge_summaries(base, generated, latest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
