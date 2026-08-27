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
from datetime import date
from pathlib import Path
from urllib.parse import urljoin,urlparse
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
EVENTS=DATA/"events.json"
S=requests.Session()
S.headers.update({
    "User-Agent":"Mozilla/5.0 (compatible; TrentinoEventsAssetBot/1.0)",
    "Accept-Language":"it-IT,it;q=.9,en;q=.7,de;q=.6"
})
INDEX_HINTS={"/","/eventi","/events","/agenda","/appuntamenti","/rassegne","/calendario","/calendario-eventi","/it/eventi","/en/events"}

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
    try:
        p=urlparse(u)
        path=(p.path or "/").rstrip("/") or "/"
        low=path.casefold()
        if low in INDEX_HINTS:return True
        parts=[x for x in path.split("/") if x]
        if parts and parts[-1].casefold() in {"eventi","events","agenda","appuntamenti","rassegne","calendario","calendario-eventi"}:return True
        return len(parts)<=1
    except:return True
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
    if title_tokens and url_hits>=max(1,min(2,len(title_tokens))): sc=max(sc,.72)
    return sc>=.56
def best_anchor(name,sp,base):
    best=(0.0,None)
    for a in sp.find_all("a",href=True):
        href=urljoin(base,a.get("href")).split("#")[0]
        if not href.startswith(("http://","https://")):continue
        text=clean(a.get_text(" ",strip=True))
        if len(text)<3:continue
        sc=similarity(name,text)
        if sc<.58:
            path=norm(urlparse(href).path.replace("/"," "))
            tokens=[x for x in norm(name).split() if len(x)>=4]
            hits=sum(1 for x in tokens if x in path)
            if tokens and hits>=max(1,min(2,len(tokens))):sc=max(sc,.64)
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
    return vals

def main():
    events=json.loads(EVENTS.read_text()) if EVENTS.exists() else []
    today=date.today(); horizon=today+relativedelta(years=1)
    changed=0
    for e in events:
        try:
            end=date.fromisoformat(e.get("endDate") or e.get("startDate"))
            start=date.fromisoformat(e.get("startDate"))
        except Exception:continue
        if end<today or start>horizon:continue
        name=display_name(e)
        if not name:continue
        current=clean(e.get("officialUrl"))
        need_link=not current or general_url(current)
        current_img=clean(e.get("image"))
        need_img=(not current_img) or "images.unsplash.com" in current_img
        if not need_link and not need_img:continue

        urls=candidate_urls(e)
        resolved=None
        resolved_sp=None
        resolved_from_child=False

        # First inspect existing candidate URLs.
        for u in urls:
            sp,final,_=fetch(u)
            if not sp:continue
            if concrete_match(name,sp,final):
                resolved=canonical(sp,final); resolved_sp=sp; break
            # General listing page: search for a matching child detail page.
            child=best_anchor(name,sp,final)
            if child:
                sp2,final2,_=fetch(child)
                if sp2 and concrete_match(name,sp2,final2):
                    resolved=canonical(sp2,final2); resolved_sp=sp2; resolved_from_child=True; break

        if not resolved:continue

        local_change=False
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
            changed+=1

    if changed:
        EVENTS.write_text(json.dumps(events,ensure_ascii=False,indent=2)+"\n")
    print(f"assetEnrichedEvents={changed}")

if __name__=="__main__":
    main()
