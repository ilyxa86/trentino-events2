#!/usr/bin/env python3
"""Conservatively enrich live events with concrete detail URLs and event-specific images.

Rules:
- prefer an event detail page over organizer/calendar homepages when one can be matched
- only use images extracted from a page that strongly matches the event
- preserve existing concrete links/images unless a clearly better event-specific page is found
- never invent URLs or imagery
"""
from __future__ import annotations
import json,re,unicodedata
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from datetime import date
from pathlib import Path
from urllib.parse import urljoin,urlparse
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from event_descriptions import enrich_descriptions, substantive, event_detail_url

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
EVENTS=DATA/"events.json"
S=requests.Session()
S.headers.update({
    "User-Agent":"Mozilla/5.0 (compatible; TrentinoEventsAssetBot/1.0)",
    "Accept-Language":"it-IT,it;q=.9,en;q=.7,de;q=.6"
})
INDEX_HINTS={"/","/eventi","/events","/agenda","/appuntamenti","/rassegne","/calendario","/calendario-eventi","/it/eventi","/en/events"}
LISTING_URLS={}

def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def norm(v):
    s="".join(c for c in unicodedata.normalize("NFKD",clean(v)) if not unicodedata.combining(c)).casefold()
    s=re.sub(r"\b20\d{2}\b"," ",s)
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()
def display_name(e):
    n=e.get("name")
    if isinstance(n,dict): return clean(n.get("it") or n.get("de") or n.get("en"))
    return clean(n)
def general_url(u):
    if not event_detail_url(u):return True
    try:
        p=urlparse(u)
        path=(p.path or "/").rstrip("/") or "/"
        low=path.casefold()
        if low in INDEX_HINTS:return True
        parts=[x for x in path.split("/") if x]
        if parts and parts[-1].casefold() in {"eventi","events","agenda","appuntamenti","rassegne","calendario","calendario-eventi"}:return True
        return len(parts)<=1
    except:return True
@lru_cache(maxsize=2000)
def fetch(u):
    try:
        r=S.get(u,timeout=25,allow_redirects=True)
        r.raise_for_status()
        if "html" not in (r.headers.get("content-type") or "").lower(): return None,None,None
        return BeautifulSoup(r.text,"html.parser"),r.url,r.text
    except Exception:return None,None,None
def page_identity(sp):
    bits=[]
    if sp.title: bits.append(clean(sp.title.get_text(" ",strip=True)))
    for tag in ["h1","h2"]:
        x=sp.find(tag)
        if x: bits.append(clean(x.get_text(" ",strip=True)))
    return " | ".join(bits[:3])
def similarity(name,text):
    a,b=norm(name),norm(text)
    if not a or not b:return 0.0
    base=SequenceMatcher(None,a,b).ratio()
    aw={x for x in a.split() if len(x)>=4}
    bw={x for x in b.split() if len(x)>=4}
    overlap=(len(aw & bw)/max(1,len(aw))) if aw else 0
    return max(base,overlap)
def concrete_match(name,sp,final):
    ident=page_identity(sp)
    sc=similarity(name,ident)
    path=norm(urlparse(final).path.replace("/"," "))
    title_tokens=[x for x in norm(name).split() if len(x)>=4]
    url_hits=sum(1 for x in title_tokens if x in path)
    if title_tokens and url_hits>=max(1,len(title_tokens)*.75) and sc>=.4: sc=max(sc,.72)
    return sc>=.56
def best_anchor(name,sp,base):
    best=(0.0,None)
    for a in sp.find_all("a",href=True):
        href=urljoin(base,a.get("href")).split("#")[0]
        if not event_detail_url(href):continue
        text=clean(a.get_text(" ",strip=True) or a.get("aria-label") or a.get("title"))
        sc=similarity(name,text)
        if sc<.58:
            path=norm(urlparse(href).path.replace("/"," "))
            tokens=[x for x in norm(name).split() if len(x)>=4]
            hits=sum(1 for x in tokens if x in path)
            if tokens and hits>=max(1,len(tokens)*.75):sc=max(sc,.72)
        if sc>best[0]:best=(sc,href)
    return best[1] if best[0]>=.64 else None
def extract_image(sp,base):
    # JSON-LD Event imagery first.
    for tag in sp.find_all("script",type="application/ld+json"):
        try:data=json.loads(tag.string or "")
        except Exception:continue
        stack=data if isinstance(data,list) else [data]
        while stack:
            obj=stack.pop()
            if isinstance(obj,list):stack.extend(obj);continue
            if not isinstance(obj,dict):continue
            graph=obj.get("@graph")
            if isinstance(graph,list):stack.extend(graph)
            typ=obj.get("@type")
            types=typ if isinstance(typ,list) else [typ]
            if any(str(t).casefold()=="event" for t in types):
                img=obj.get("image")
                if isinstance(img,str) and img:return urljoin(base,img)
                if isinstance(img,list) and img:
                    x=img[0]
                    if isinstance(x,str):return urljoin(base,x)
                    if isinstance(x,dict) and x.get("url"):return urljoin(base,x["url"])
                if isinstance(img,dict) and img.get("url"):return urljoin(base,img["url"])
    for attrs in [
        {"property":"og:image"},
        {"name":"twitter:image"},
        {"property":"twitter:image"},
    ]:
        x=sp.find("meta",attrs=attrs)
        if x and x.get("content"):return urljoin(base,x["content"])
    x=sp.find("link",rel=lambda v:v and "image_src" in v)
    if x and x.get("href"):return urljoin(base,x["href"])
    return None
def canonical(sp,final):
    x=sp.find("link",rel=lambda v:v and "canonical" in v)
    if x and x.get("href"):
        u=urljoin(final,x["href"])
        if u.startswith(("http://","https://")):return u
    return final

def candidate_urls(e):
    vals=[]
    for u in [e.get("officialUrl"),*(e.get("sourceUrls") or [])]:
        u=clean(u)
        if u and u.startswith(("http://","https://")) and u not in vals:vals.append(u)
    # A saved pagination URL can now contain different events. Search the other
    # known pages of that official calendar before declaring the detail missing.
    for hostname in {urlparse(u).hostname for u in vals}:
        for u in LISTING_URLS.get(hostname,[]):
            if u not in vals:vals.append(u)
    return vals

@lru_cache(maxsize=30)
def sitemap_links(hostname):
    """Use only sitemaps declared by the official site itself."""
    root="https://"+hostname
    try:
        response=S.get(root+"/robots.txt",timeout=15)
        response.raise_for_status()
        pending=re.findall(r"^Sitemap:\s*(https?://\S+)",response.text,re.M|re.I)
        seen=set(); links=[]
        while pending and len(seen)<6:
            url=pending.pop(0)
            if url in seen or urlparse(url).hostname!=hostname:continue
            seen.add(url)
            response=S.get(url,timeout=15);response.raise_for_status()
            xml=BeautifulSoup(response.content,"xml")
            locs=[clean(tag.get_text()) for tag in xml.find_all("loc")]
            if xml.find("sitemapindex"):
                pending.extend(locs)
            else:
                links.extend(u for u in locs if urlparse(u).hostname==hostname and event_detail_url(u)
                             and re.search(r"/(events|eventi|appuntamenti|rassegne)/",urlparse(u).path,re.I))
        return links
    except requests.RequestException:return []

def matching_sitemap_urls(name,hostname):
    scored=[]
    for url in sitemap_links(hostname):
        slug=re.sub(r"[_-]\d+$","",urlparse(url).path.rstrip("/").split("/")[-1])
        score=similarity(name,slug)
        if score>=.75:scored.append((score,url))
    return [url for score,url in sorted(scored,reverse=True)[:5]]

def main():
    events=json.loads(EVENTS.read_text(encoding="utf-8")) if EVENTS.exists() else []
    LISTING_URLS.clear()
    for event in events:
        for u in [event.get("officialUrl"),*(event.get("sourceUrls") or [])]:
            if u and general_url(u) and re.search(r"/(?:events|eventi|agenda|appuntamenti|calendario|rassegne)(?:/|$)",urlparse(u).path,re.I):
                known=LISTING_URLS.setdefault(urlparse(u).hostname,[])
                if u not in known:known.append(u)
    today=date.today(); horizon=today+relativedelta(years=1)
    def enrich(e):
        try:
            end=date.fromisoformat(e.get("endDate") or e.get("startDate"))
            start=date.fromisoformat(e.get("startDate"))
        except Exception:return False
        if end<today or start>horizon:return False
        name=display_name(e)
        if not name:return False
        current=clean(e.get("officialUrl"))
        need_link=not current or general_url(current)
        current_img=clean(e.get("image"))
        need_img=(not current_img) or "images.unsplash.com" in current_img
        descriptions=e.get("description") or {}
        need_summary=not all(substantive(descriptions.get(lang)) for lang in ("de","en","it"))
        if not need_link and not need_img and not need_summary:return False

        urls=candidate_urls(e)
        resolved=None
        resolved_sp=None
        resolved_from_child=False

        # First inspect existing candidate URLs.
        for u in urls:
            sp,final,_=fetch(u)
            if not sp:continue
            if not general_url(final) and concrete_match(name,sp,final):
                resolved=canonical(sp,final); resolved_sp=sp; break
            # General listing page: search for a matching child detail page.
            child=best_anchor(name,sp,final)
            if child:
                sp2,final2,_=fetch(child)
                if sp2 and not general_url(final2) and concrete_match(name,sp2,final2):
                    resolved=canonical(sp2,final2); resolved_sp=sp2; resolved_from_child=True; break

        if not resolved:
            for hostname in sorted({urlparse(u).hostname for u in urls if urlparse(u).hostname}):
                for u in matching_sitemap_urls(name,hostname):
                    sp,final,_=fetch(u)
                    if sp and not general_url(final) and concrete_match(name,sp,final):
                        resolved=canonical(sp,final);resolved_sp=sp;resolved_from_child=True;break
                if resolved:break
        if not resolved:return False

        local_change=False
        if need_summary:
            local_change=enrich_descriptions(e,resolved_sp,resolved,fetch)
            if local_change:e["descriptionVerified"]=today.isoformat()
        if resolved and not general_url(resolved) and (need_link or resolved_from_child):
            if resolved!=current:
                e["officialUrl"]=resolved
                urls2=set(e.get("sourceUrls") or [])
                if current:urls2.add(current)
                urls2.add(resolved)
                e["sourceUrls"]=sorted(urls2)
                local_change=True

        if need_img and resolved_sp:
            img=extract_image(resolved_sp,resolved)
            if img and not img.lower().endswith((".svg",".ico")):
                if img!=current_img:
                    e["image"]=img
                    e["imageSourceUrl"]=resolved
                    local_change=True

        if local_change:
            e["assetVerified"]=today.isoformat()
        return local_change

    changed=0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i,result in enumerate(pool.map(enrich,events),1):
            changed+=bool(result)
            if i%50==0:print(f"enrichmentProgress={i}/{len(events)} changed={changed}",flush=True)

    if changed:
        EVENTS.write_text(json.dumps(events,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"assetEnrichedEvents={changed}")

if __name__=="__main__":
    main()
