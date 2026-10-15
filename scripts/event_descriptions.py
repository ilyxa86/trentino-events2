"""Source-backed, language-aware event summaries shared by import and enrichment.

Never manufacture a description from a title, category, place or dates. Missing
source copy stays missing until a matching detail page supplies real content.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

PLACEHOLDER = re.compile(
    r"Aktuelle Details finden Sie|See the official event page|Consulta la pagina ufficiale|"
    r"This gives you the key timing|So sind Zeitraum und Ort|In questo modo data e luogo|"
    r"^Local event notice in |^Lokaler Veranstaltungshinweis in |^Segnalazione di un evento locale a ",
    re.I,
)


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def substantive(value):
    return len(clean(value)) >= 40 and not PLACEHOLDER.search(clean(value))


def summarize(value, max_chars=560):
    """A short extract, keeping sentence boundaries and avoiding HTML/navigation."""
    text = clean(BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True))
    if not substantive(text):
        return ""
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý“„\"])", text)
    selected = []
    for sentence in sentences:
        if selected and len(" ".join(selected + [sentence])) > max_chars:
            break
        selected.append(sentence)
        if len(selected) == 2:
            break
    result = " ".join(selected)
    if len(result) > max_chars:
        result = result[:max_chars - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return result


def page_language(sp, url):
    lang = clean((sp.html or {}).get("lang")).lower()[:2]
    if lang in {"de", "en", "it"}:
        return lang
    match = re.search(r"/(de|en|it|eng|deu)(?:/|$)", urlparse(url).path)
    return {"eng": "en", "deu": "de"}.get(match[1], match[1]) if match else "it"


def extract_description(sp):
    # Event-specific structured copy, never descriptions of unrelated graph nodes.
    for tag in sp.select('script[type="application/ld+json"]'):
        try:
            stack = [json.loads(tag.string or tag.get_text())]
        except (ValueError, TypeError):
            continue
        while stack:
            obj = stack.pop()
            if isinstance(obj, list):
                stack.extend(obj)
            elif isinstance(obj, dict):
                stack.extend(obj.get("@graph", []))
                types = obj.get("@type", [])
                if isinstance(types, str):
                    types = [types]
                if any(t == "Event" or str(t).endswith("Event") for t in types):
                    description = summarize(obj.get("description"))
                    if description:
                        return description

    # The body intro is usually richer than SEO copy. These containers exclude
    # booking forms, navigation, calendars and related-event lists.
    for selector in [".descrizione", "article.primary .desc", '[itemprop="description"]',
                     ".event-description", ".event__description", ".description-text"]:
        container = sp.select_one(selector)
        if not container:
            continue
        paragraphs = [clean(p.get_text(" ", strip=True)) for p in container.select("p")]
        paragraphs = [p for p in paragraphs if substantive(p)]
        description = summarize(" ".join(paragraphs[:2]) if paragraphs else container.get_text(" ", strip=True))
        if description:
            return description

    for selector in ['meta[name="description"]', 'meta[property="og:description"]']:
        tag = sp.select_one(selector)
        description = summarize(tag.get("content")) if tag else ""
        if description:
            return description
    return ""


def enrich_descriptions(event, sp, url, fetch):
    """Called only after the detail page has been matched to this event."""
    descriptions = event.get("description")
    descriptions = dict(descriptions) if isinstance(descriptions, dict) else {}
    sources = dict(event.get("descriptionSources") or {})
    language = page_language(sp, url)
    changed = False
    pages = {language: (sp, url)}
    # Follow only declared language alternatives on the same official site.
    for link in sp.select("[hreflang][href]"):
        lang = link.get("hreflang", "")[:2].lower()
        alternate = urljoin(url, link["href"])
        if lang not in {"de", "en", "it"} or lang in pages or substantive(descriptions.get(lang)):
            continue
        if urlparse(alternate).hostname != urlparse(url).hostname:
            continue
        other, final, _ = fetch(alternate)
        if other and page_language(other, final) == lang:
            pages[lang] = (other, final)
    for lang, (page, source) in pages.items():
        if substantive(descriptions.get(lang)):
            continue  # Preserve manually curated/transformed translations.
        description = extract_description(page)
        if description:
            descriptions[lang] = description
            sources[lang] = source
            changed = True
    # Remove old boilerplate even when a source is temporarily inaccessible.
    descriptions = {lang: value for lang, value in descriptions.items() if substantive(value)}
    if descriptions != event.get("description"):
        event["description"] = descriptions
        changed = True
    if sources:
        event["descriptionSources"] = sources
    event["descriptionStatus"] = "complete" if all(substantive(descriptions.get(l)) for l in ("de", "en", "it")) else "partial" if descriptions else "missing"
    return changed
