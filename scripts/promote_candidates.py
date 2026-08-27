#!/usr/bin/env python3
"""Promote deterministic crawler candidates into the live event database.

This is deliberately conservative: it only promotes candidates whose dates can
be parsed reliably and whose interval overlaps the rolling 12-month window.
Previously missed records are coverage backfills (status=null), not NEW alerts.
Existing curated events are preserved and enriched rather than replaced.
"""
from __future__ import annotations

import calendar
import json
import re
import unicodedata
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path

from dateutil.relativedelta import relativedelta

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CANDIDATES = DATA / "discovered_candidates.json"
EVENTS = DATA / "events.json"

MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))

ROVERETO_AREA = {
    "rovereto", "isera", "mori", "ala", "avio", "brentonico", "villa lagarina",
    "nogaredo", "pomarolo", "volano", "calliano", "besenello", "nomi", "terragnolo",
    "vallarsa", "ronzo-chienis", "ronzo chienis", "trambileno", "marco di rovereto"
}
TRENTO_AREA = {"trento", "lavis", "aldeno", "cimone", "garniga terme"}
GARDA_AREA = {
    "riva del garda", "arco", "nago-torbole", "nago torbole", "torbole", "tenno",
    "ledro", "dro", "drena"
}

# Practical Rovereto-centered scope requested by the user. This is deliberately
# conservative: ambiguous province-wide candidates are not auto-promoted until
# a municipality can be resolved inside the roughly 80 km travel radius.
IN_SCOPE_PLACES = {
    *ROVERETO_AREA, *TRENTO_AREA, *GARDA_AREA,
    "stenico", "comano terme", "fiavè", "fiave", "tione di trento",
    "san lorenzo dorsino", "bondone", "lavarone", "folgaria", "luserna",
    "pergine valsugana", "levico terme", "caldonazzo", "calceranica al lago",
    "andalo", "molveno", "fai della paganella", "cavedago", "spormaggiore",
    "mezzolombardo", "mezzocorona", "san michele all'adige", "cembra",
    "altavalle", "grumes", "faedo", "vezzano", "vallelaghi", "calavino",
    "lasino", "padergnone"
}
OUT_OF_SCOPE_SOURCE_IDS = {"val_di_sole_events", "val_di_fassa_events", "san_martino_primiero_events"}


KNOWN_PLACES = sorted({
    *ROVERETO_AREA, *TRENTO_AREA, *GARDA_AREA,
    "moena", "predazzo", "cavalese", "tesero", "ziano di fiemme", "canazei", "campitello di fassa",
    "pozza di fassa", "san giovanni di fassa", "soraga", "san martino di castrozza", "fiera di primiero",
    "primiero-tonadico", "primiero tonadico", "mezzano", "imèr", "imer", "transacqua", "levico terme",
    "pergine valsugana", "borgo valsugana", "caldonazzo", "calceranica al lago", "castello tesino",
    "pieve tesino", "bieno", "andalo", "molveno", "fai della paganella", "cavedago", "spormaggiore",
    "mezzolombardo", "mezzocorona", "san michele all'adige", "cles", "coredo", "tavon", "predaia",
    "romeno", "fondo", "ville d'anaunia", "dimaro", "folgarida", "madonna di campiglio", "pinzolo",
    "pellizzano", "ossana", "passo del tonale", "peio", "malè", "male", "commezzadura", "rabbi",
    "stenico", "comano terme", "fiavè", "fiave", "tione di trento", "san lorenzo dorsino", "bondone",
    "lavarone", "folgaria", "luserna", "cembra", "altavalle", "grumes", "faedo", "vezzano",
    "vallelaghi", "calavino", "lasino", "dro", "padergnone"
}, key=len, reverse=True)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_accents(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))


def norm(value: object) -> str:
    s = strip_accents(clean(value)).casefold()
    s = re.sub(r"\b20\d{2}\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slug(value: str) -> str:
    s = norm(value).replace(" ", "-")
    return s[:72].strip("-") or "event"


def iso(d: date) -> str:
    return d.isoformat()


def safe_date(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def parse_numeric(token: str) -> date | None:
    token = token.strip()
    if re.fullmatch(r"20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}", token):
        y, m, d = map(int, re.split(r"[-/.]", token))
        return safe_date(y, m, d)
    m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})", token)
    if m:
        d, mo, y = map(int, m.groups())
        return safe_date(y, mo, d)
    return None


def parse_textual_range(text: str, default_year: int) -> tuple[date, date] | None:
    low = strip_accents(text).casefold()
    month_alias = {strip_accents(k): v for k, v in MONTHS.items()}
    mre = "|".join(sorted(month_alias, key=len, reverse=True))

    # "dal 19 giugno al 28 agosto 2026" / "da sabato 2 maggio a sabato 12 dicembre 2026"
    p = re.search(rf"(?:dal|da)\s+(?:\w+\s+)?(\d{{1,2}})\s+({mre})\s+(?:al|a)\s+(?:\w+\s+)?(\d{{1,2}})\s+({mre})\s+(20\d{{2}})", low)
    if p:
        d1, m1, d2, m2, y = p.groups()
        a = safe_date(int(y), month_alias[m1], int(d1)); b = safe_date(int(y), month_alias[m2], int(d2))
        if a and b: return (a, b)

    # "dal 3 al 12 settembre 2026"
    p = re.search(rf"(?:dal|da)\s+(\d{{1,2}})\s+(?:al|a)\s+(\d{{1,2}})\s+({mre})\s+(20\d{{2}})", low)
    if p:
        d1, d2, mo, y = p.groups(); m = month_alias[mo]
        a = safe_date(int(y), m, int(d1)); b = safe_date(int(y), m, int(d2))
        if a and b: return (a, b)

    # "venerdi 28 e sabato 29 agosto [2026]"
    p = re.search(rf"(?:lunedi|martedi|mercoledi|giovedi|venerdi|sabato|domenica)?\s*(\d{{1,2}})\s+e\s+(?:lunedi|martedi|mercoledi|giovedi|venerdi|sabato|domenica)?\s*(\d{{1,2}})\s+({mre})(?:\s+(20\d{{2}}))?", low)
    if p:
        d1, d2, mo, y = p.groups(); year = int(y or default_year); m = month_alias[mo]
        a = safe_date(year, m, int(d1)); b = safe_date(year, m, int(d2))
        if a and b: return (a, b)

    # "da giugno a settembre 2026"
    p = re.search(rf"(?:dal|da)\s+({mre})\s+(?:al|a)\s+({mre})\s+(20\d{{2}})", low)
    if p:
        m1, m2, y = p.groups(); y = int(y); a_m = month_alias[m1]; b_m = month_alias[m2]
        return date(y, a_m, 1), date(y, b_m, calendar.monthrange(y, b_m)[1])

    # "di luglio e agosto 2026"
    p = re.search(rf"(?:di|tra)\s+({mre})\s+e\s+({mre})\s+(20\d{{2}})", low)
    if p:
        m1, m2, y = p.groups(); y = int(y); a_m = month_alias[m1]; b_m = month_alias[m2]
        return date(y, a_m, 1), date(y, b_m, calendar.monthrange(y, b_m)[1])

    # One explicit textual date, e.g. "sabato 5 settembre [2026]"
    p = re.search(rf"(?:lunedi|martedi|mercoledi|giovedi|venerdi|sabato|domenica)?\s*(\d{{1,2}})\s+({mre})(?:\s+(20\d{{2}}))?", low)
    if p:
        d, mo, y = p.groups(); year = int(y or default_year)
        a = safe_date(year, month_alias[mo], int(d))
        if a: return a, a

    return None


def parse_range(text: str, default_year: int) -> tuple[date, date] | None:
    tokens = re.findall(r"20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]20\d{2}", text)
    parsed = [d for d in (parse_numeric(t) for t in tokens) if d]
    # Listing cards normally put their canonical numeric dates at the end; use the last pair.
    if len(parsed) >= 2:
        a, b = parsed[-2], parsed[-1]
        if b < a: a, b = b, a
        return a, b
    if len(parsed) == 1:
        return parsed[0], parsed[0]
    return parse_textual_range(text, default_year)


def infer_place(text: str, source_id: str) -> str:
    low = strip_accents(text).casefold()
    for p in KNOWN_PLACES:
        if re.search(rf"(?<![a-z]){re.escape(strip_accents(p))}(?![a-z])", low):
            # Restore common display forms.
            return {
                "primiero-tonadico": "Primiero-Tonadico", "nago-torbole": "Nago-Torbole",
                "ronzo-chienis": "Ronzo-Chienis", "san michele all'adige": "San Michele all'Adige",
                "riva del garda": "Riva del Garda", "san martino di castrozza": "San Martino di Castrozza",
                "fiera di primiero": "Fiera di Primiero", "passo del tonale": "Passo del Tonale",
                "madonna di campiglio": "Madonna di Campiglio", "borgo valsugana": "Borgo Valsugana",
                "pergine valsugana": "Pergine Valsugana", "levico terme": "Levico Terme",
                "castello tesino": "Castello Tesino", "pieve tesino": "Pieve Tesino",
                "fai della paganella": "Fai della Paganella", "villa lagarina": "Villa Lagarina",
                "tione di trento": "Tione di Trento", "comano terme": "Comano Terme",
                "san lorenzo dorsino": "San Lorenzo Dorsino", "luserna": "Luserna",
            }.get(p, " ".join(w.capitalize() for w in p.split()))
    if source_id.startswith("visitrovereto") or source_id == "comune_rovereto_events":
        return "Rovereto/Vallagarina"
    if source_id == "comune_trento_events":
        return "Trento"
    return "Trentino"


def place_in_scope(place: str, source_id: str) -> bool:
    if source_id in OUT_OF_SCOPE_SOURCE_IDS:
        return False
    p = norm(place)
    if not p or p == "trentino":
        return False
    return any(norm(x) == p for x in IN_SCOPE_PLACES)


def infer_area(place: str, source_id: str) -> str:
    n = norm(place)
    if any(norm(p) == n for p in ROVERETO_AREA) or source_id.startswith("visitrovereto") or source_id == "comune_rovereto_events":
        return "Rovereto & Vallagarina"
    if any(norm(p) == n for p in TRENTO_AREA) or source_id == "comune_trento_events":
        return "Trento"
    if any(norm(p) == n for p in GARDA_AREA):
        return "Alto Garda"
    return "Other Trentino"


def infer_category(text: str) -> str:
    t = norm(text)
    if any(k in t for k in ["mercato", "shopping", "sbaracco"]): return "Markets & Shopping"
    if any(k in t for k in ["enogastr", "vino", "wine", "cantin", "degust", "birr", "trentodoc"]): return "Wine & Gastronomy"
    if any(k in t for k in ["agricolt", "transuman", "desmonteg", "desmalg", "malga", "allevator", "folklore"]): return "Agriculture & Tradition"
    if any(k in t for k in ["sport", "running", "marcialonga", "bike", "cicl", "ferrata", "gara", "atlet"]): return "Sport & Outdoor"
    if any(k in t for k in ["cinema", "film"]): return "Film & Culture"
    if any(k in t for k in ["danza", "dance", "teatro"]): return "Culture & Dance"
    if any(k in t for k in ["musica", "concerto", "concert"]): return "Culture & Music"
    if any(k in t for k in ["mostra", "museo", "arte", "cultur", "biblioteca"]): return "Culture & Exhibition"
    if any(k in t for k in ["bambin", "famigl", "family"]): return "Family & Culture"
    if any(k in t for k in ["congress", "conferenz", "business", "network"]): return "Business & Networking"
    if any(k in t for k in ["fiera", "expo"]): return "Trade Fair"
    if any(k in t for k in ["festa", "sagra", "festival", "palio"]): return "Festival"
    return "Other"


def extract_time(text: str) -> str | None:
    m = re.search(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)", text)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def generic_description(title: str, place: str) -> dict[str, str]:
    where_de = f" in {place}" if place and place != "Trentino" else " im Trentino"
    where_en = f" in {place}" if place and place != "Trentino" else " in Trentino"
    where_it = f" a {place}" if place and place != "Trentino" else " in Trentino"
    return {
        "de": f"Veranstaltung „{title}“{where_de}. Aktuelle Details finden Sie auf der offiziellen Veranstaltungsseite.",
        "en": f"“{title}” event{where_en}. See the official event page for the latest details.",
        "it": f"Evento “{title}”{where_it}. Consulta la pagina ufficiale per i dettagli aggiornati.",
    }


def display_name(event: dict) -> str:
    name = event.get("name")
    if isinstance(name, dict):
        return clean(name.get("it") or name.get("de") or name.get("en"))
    return clean(name)


def source_urls(event: dict) -> set[str]:
    vals = set()
    for u in event.get("sourceUrls") or []:
        if u: vals.add(clean(u))
    if event.get("officialUrl"): vals.add(clean(event["officialUrl"]))
    return vals


def main() -> None:
    payload = json.loads(CANDIDATES.read_text()) if CANDIDATES.exists() else {"records": []}
    events = json.loads(EVENTS.read_text()) if EVENTS.exists() else []
    generated = payload.get("generatedAt") or datetime.utcnow().isoformat() + "Z"
    try:
        run_day = datetime.fromisoformat(generated.replace("Z", "+00:00")).date()
    except ValueError:
        run_day = date.today()
    horizon = run_day + relativedelta(years=1)

    # Preserve manually curated records, while making German available where it was missing.
    for e in events:
        nm = display_name(e)
        if isinstance(e.get("name"), dict) and nm:
            e["name"].setdefault("de", nm)
        if isinstance(e.get("description"), dict) and "de" not in e["description"]:
            e["description"]["de"] = e["description"].get("en") or e["description"].get("it") or ""

    candidates = []
    for r in payload.get("records") or []:
        title = clean(r.get("title"))
        raw = clean(r.get("rawText"))
        if not title or len(title) < 2:
            continue
        dates = parse_range(raw, run_day.year)
        if not dates:
            continue
        start, end = dates
        if end < run_day or start > horizon:
            continue
        sid = clean(r.get("sourceId"))
        place = infer_place(raw, sid)
        if not place_in_scope(place, sid):
            continue
        area = infer_area(place, sid)
        detail = clean(r.get("detailUrl") or r.get("pageUrl"))
        candidate = {
            "title": title,
            "startDate": iso(start), "endDate": iso(end),
            "startTime": extract_time(raw),
            "municipality": place, "area": area,
            "venue": place if place != "Trentino" else None,
            "category": infer_category(raw),
            "image": clean(r.get("image")) or None,
            "officialUrl": detail,
            "source": clean(r.get("sourceName")) or sid,
            "sourceId": sid,
        }
        candidates.append(candidate)

    # Deduplicate the enumerator feed before touching the curated DB.
    grouped: dict[tuple[str, str, str, str], dict] = {}
    for c in candidates:
        key = (norm(c["title"]), c["startDate"], c["endDate"], norm(c["municipality"]))
        if key not in grouped:
            grouped[key] = c | {"sourceUrls": set([c["officialUrl"]] if c["officialUrl"] else [])}
        else:
            g = grouped[key]
            if c.get("image") and not g.get("image"): g["image"] = c["image"]
            if c.get("officialUrl"): g["sourceUrls"].add(c["officialUrl"])
            # Prefer a more specific place over the generic Trentino fallback.
            if g.get("municipality") == "Trentino" and c.get("municipality") != "Trentino":
                g["municipality"], g["area"], g["venue"] = c["municipality"], c["area"], c["venue"]

    existing_index = []
    for i, e in enumerate(events):
        try:
            s, en = e.get("startDate"), e.get("endDate") or e.get("startDate")
            existing_index.append((i, norm(display_name(e)), s, en, norm(e.get("municipality"))))
        except Exception:
            pass

    added = enriched = 0
    used_ids = {clean(e.get("id")) for e in events if e.get("id")}

    for c in sorted(grouped.values(), key=lambda x: (x["startDate"], norm(x["title"]))):
        best = None
        best_score = 0.0
        nt = norm(c["title"])
        np = norm(c["municipality"])
        for i, et, s, en, ep in existing_index:
            if s != c["startDate"] or en != c["endDate"]:
                continue
            score = SequenceMatcher(None, nt, et).ratio()
            if np and ep and np == ep: score += 0.08
            if score > best_score:
                best_score, best = score, i
        if best is not None and best_score >= 0.84:
            e = events[best]
            changed = False
            if c.get("image") and not e.get("image"):
                e["image"] = c["image"]; changed = True
            urls = source_urls(e) | c["sourceUrls"]
            if urls and sorted(urls) != sorted(e.get("sourceUrls") or []):
                e["sourceUrls"] = sorted(urls); changed = True
            if not e.get("officialUrl") and c.get("officialUrl"):
                e["officialUrl"] = c["officialUrl"]; changed = True
            if changed:
                e["verified"] = iso(run_day); enriched += 1
            continue

        eid_base = f"{slug(c['title'])}-{c['startDate'][:4]}"
        eid = eid_base
        n = 2
        while eid in used_ids:
            eid = f"{eid_base}-{n}"; n += 1
        used_ids.add(eid)
        ev = {
            "id": eid,
            "name": {"de": c["title"], "en": c["title"], "it": c["title"]},
            "startDate": c["startDate"], "endDate": c["endDate"], "startTime": c["startTime"],
            "municipality": c["municipality"], "area": c["area"], "venue": c["venue"],
            "category": c["category"], "status": None, "confirmed": True,
            "description": generic_description(c["title"], c["municipality"]),
            "organizer": None, "price": "See official page",
            "officialUrl": c["officialUrl"], "source": c["source"],
            "verified": iso(run_day), "discoveredVia": "coverage_backfill",
            "confidence": "official-calendar",
        }
        if c.get("image"): ev["image"] = c["image"]
        if c["sourceUrls"]: ev["sourceUrls"] = sorted(c["sourceUrls"])
        events.append(ev)
        existing_index.append((len(events)-1, nt, c["startDate"], c["endDate"], np))
        added += 1

    events.sort(key=lambda e: (e.get("startDate") or "9999-99-99", norm(display_name(e))))
    EVENTS.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n")
    print(f"candidateRecords={len(payload.get('records') or [])} parsableInWindow={len(candidates)} canonicalCandidates={len(grouped)} addedBackfills={added} enrichedExisting={enriched} totalEvents={len(events)}")


if __name__ == "__main__":
    main()
