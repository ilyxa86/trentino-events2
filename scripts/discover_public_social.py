#!/usr/bin/env python3
"""Discover public Facebook-linked events through OpenAI web search.

This job never logs into Facebook. It searches only the public web for posts,
public pages, indexed references and corroborating public sources connected to
the Facebook communities listed in data/facebook_sources.json.

The script is intentionally conservative:
- only Rovereto-centered ~80 km practical travel scope
- only dated events inside the rolling 12-month window
- existing official events are not re-labelled as Facebook events
- newly found Facebook-primary records use sourceType='facebook'
- older/uncertain discoveries are coverage backfills, not noisy NEW alerts
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher

from dateutil.relativedelta import relativedelta
from openai import OpenAI

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
SOURCES=DATA/"facebook_sources.json"
EVENTS=DATA/"events.json"
CANDIDATES=DATA/"facebook_candidates.json"
DELTA=DATA/"social_delta.json"

IN_SCOPE={
"rovereto","rovereto/vallagarina","isera","mori","ala","avio","brentonico","villa lagarina",
"nogaredo","pomarolo","volano","calliano","besenello","nomi","terragnolo","vallarsa","ronzo-chienis",
"trambileno","trento","lavis","aldeno","cimone","garniga terme","riva del garda","arco","nago-torbole",
"torbole","tenno","ledro","dro","drena","stenico","comano terme","fiave","tione di trento",
"san lorenzo dorsino","bondone","lavarone","folgaria","luserna","pergine valsugana","levico terme",
"caldonazzo","calceranica al lago","andalo","molveno","fai della paganella","cavedago","spormaggiore",
"mezzolombardo","mezzocorona","san michele all'adige","cembra","altavalle","grumes","faedo","vezzano",
"vallelaghi","calavino","lasino","padergnone"
}

def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def norm(v):
    s="".join(c for c in unicodedata.normalize("NFKD",clean(v)) if not unicodedata.combining(c)).casefold()
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return re.sub(r"\s+"," ",s).strip()
def slug(v):
    return norm(v).replace(" ","-")[:64].strip("-") or "event"
def parse_day(v):
    try:return date.fromisoformat(clean(v))
    except:return None
def in_scope(place):
    p=norm(place)
    return p in {norm(x) for x in IN_SCOPE}
def display_name(e):
    n=e.get("name")
    if isinstance(n,dict): return clean(n.get("de") or n.get("it") or n.get("en"))
    return clean(n)

def parse_json(text):
    text=clean(text)
    a=text.find("{"); b=text.rfind("}")
    if a<0 or b<a: return {"events":[]}
    try:return json.loads(text[a:b+1])
    except:return {"events":[]}

def prompt_for(src,run_day,horizon):
    return f"""Search the PUBLIC WEB only for upcoming local events connected to this Facebook community/page:
NAME: {src['name']}
PLACE: {src['place']}
DISCOVERY QUERY: {src.get('discoveryQuery','')}

Important:
- Do NOT log into Facebook and do not use private/inaccessible posts.
- Search public/indexed Facebook references, public event pages, local news, municipality/Pro Loco/organizer pages and public flyers.
- Geography is limited to roughly 80 km practical travel distance from Rovereto, Italy.
- Date window: {run_day.isoformat()} through {horizon.isoformat()}.
- Return only real dated events with enough evidence to identify date and municipality.
- Do not invent details. If only Facebook/public-social evidence exists, confirmed=false is acceptable.
- announcementDate is the public announcement/post/publication date if you can determine it; otherwise null.
- publicUrl should be the best public evidence URL you actually found. Prefer an official organizer/municipality URL when available, otherwise a public indexed page referencing the Facebook announcement.
- imageUrl only when a reliable public event-specific image URL is available.
- Keep descriptions concise and factual.

Return JSON only, no markdown:
{{
  "events":[
    {{
      "name":"...",
      "startDate":"YYYY-MM-DD",
      "endDate":"YYYY-MM-DD",
      "startTime":"HH:MM or null",
      "municipality":"...",
      "venue":"... or null",
      "category":"...",
      "descriptionDe":"...",
      "descriptionEn":"...",
      "descriptionIt":"...",
      "organizer":"... or null",
      "price":"... or null",
      "publicUrl":"https://...",
      "imageUrl":"https://... or null",
      "announcementDate":"YYYY-MM-DD or null",
      "confirmed":true,
      "confidence":"official-corroborated | public-social-corroborated | public-social-only"
    }}
  ]
}}"""

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY missing; public Facebook discovery skipped.")
        return
    sources=json.loads(SOURCES.read_text()).get("sources",[])
    events=json.loads(EVENTS.read_text()) if EVENTS.exists() else []
    run_day=date.today(); horizon=run_day+relativedelta(years=1)
    client=OpenAI()
    model=os.getenv("OPENAI_SOCIAL_MODEL","gpt-5-mini")
    raw_records=[]

    for src in sources:
        try:
            resp=client.responses.create(
                model=model,
                tools=[{"type":"web_search","search_context_size":"low"}],
                input=prompt_for(src,run_day,horizon)
            )
            payload=parse_json(resp.output_text)
        except Exception as exc:
            print(f"{src['id']}: discovery failed: {exc}")
            continue
        for item in payload.get("events") or []:
            item["facebookSourceId"]=src["id"]
            item["facebookSourceName"]=src["name"]
            raw_records.append(item)

    valid=[]
    for x in raw_records:
        a=parse_day(x.get("startDate")); b=parse_day(x.get("endDate") or x.get("startDate"))
        if not a or not b: continue
        if b<run_day or a>horizon: continue
        if not in_scope(x.get("municipality")): continue
        if not clean(x.get("name")) or not clean(x.get("publicUrl")): continue
        x["startDate"]=a.isoformat(); x["endDate"]=b.isoformat()
        valid.append(x)

    # Canonicalize the current social scan.
    dedup={}
    for x in valid:
        key=(norm(x["name"]),x["startDate"],x["endDate"],norm(x["municipality"]))
        if key not in dedup or (x.get("confirmed") and not dedup[key].get("confirmed")):
            dedup[key]=x
    candidates=list(dedup.values())
    CANDIDATES.write_text(json.dumps({"generatedAt":datetime.utcnow().isoformat()+"Z","records":candidates},ensure_ascii=False,indent=2)+"\n")

    existing=[]
    for i,e in enumerate(events):
        existing.append((i,norm(display_name(e)),e.get("startDate"),e.get("endDate") or e.get("startDate"),norm(e.get("municipality"))))

    added=[]; used={clean(e.get("id")) for e in events if e.get("id")}
    for c in sorted(candidates,key=lambda x:(x["startDate"],norm(x["name"]))):
        best=None; score=0.0
        for i,n,s,en,p in existing:
            if s!=c["startDate"] or en!=c["endDate"]: continue
            sc=SequenceMatcher(None,norm(c["name"]),n).ratio()
            if p==norm(c["municipality"]): sc+=0.08
            if sc>score: score,best=sc,i
        if best is not None and score>=0.84:
            # Existing official/calendar record wins. Add corroborating source URL only.
            e=events[best]
            urls=set(e.get("sourceUrls") or [])
            urls.add(clean(c["publicUrl"]))
            e["sourceUrls"]=sorted(u for u in urls if u)
            continue

        base=f"fb-{slug(c['name'])}-{c['startDate'][:4]}"
        eid=base; n=2
        while eid in used:
            eid=f"{base}-{n}"; n+=1
        used.add(eid)

        ann=parse_day(c.get("announcementDate"))
        genuinely_new=bool(ann and ann>=run_day-timedelta(days=1))
        ev={
            "id":eid,
            "name":{"de":clean(c["name"]),"en":clean(c["name"]),"it":clean(c["name"])},
            "startDate":c["startDate"],"endDate":c["endDate"],"startTime":clean(c.get("startTime")) or None,
            "municipality":clean(c["municipality"]),"area":"Facebook / Local","venue":clean(c.get("venue")) or clean(c["municipality"]),
            "category":clean(c.get("category")) or "Other",
            "status":"NEW" if genuinely_new else None,
            "statusDate":run_day.isoformat() if genuinely_new else None,
            "confirmed":bool(c.get("confirmed")),
            "description":{
                "de":clean(c.get("descriptionDe")) or f"Lokaler Veranstaltungshinweis in {clean(c['municipality'])}.",
                "en":clean(c.get("descriptionEn")) or f"Local event notice in {clean(c['municipality'])}.",
                "it":clean(c.get("descriptionIt")) or f"Segnalazione di un evento locale a {clean(c['municipality'])}."
            },
            "organizer":clean(c.get("organizer")) or None,
            "price":clean(c.get("price")) or "See source",
            "officialUrl":clean(c["publicUrl"]),
            "source":clean(c.get("facebookSourceName")) or "Public Facebook discovery",
            "sourceType":"facebook",
            "sourceUrls":[clean(c["publicUrl"])],
            "verified":run_day.isoformat(),
            "discoveredVia":"facebook_public_web" if genuinely_new else "facebook_backfill",
            "confidence":clean(c.get("confidence")) or "public-social-only"
        }
        if clean(c.get("imageUrl")): ev["image"]=clean(c["imageUrl"])
        events.append(ev)
        existing.append((len(events)-1,norm(c["name"]),c["startDate"],c["endDate"],norm(c["municipality"])))
        added.append(ev)

    events.sort(key=lambda e:(e.get("startDate") or "9999-99-99",norm(display_name(e))))
    EVENTS.write_text(json.dumps(events,ensure_ascii=False,indent=2)+"\n")
    DELTA.write_text(json.dumps({
        "generatedAt":datetime.utcnow().isoformat()+"Z",
        "newFacebookEvents":[{"id":e["id"],"name":display_name(e),"date":e["startDate"],"municipality":e["municipality"]} for e in added if e.get("status")=="NEW"],
        "facebookBackfills":[{"id":e["id"],"name":display_name(e),"date":e["startDate"],"municipality":e["municipality"]} for e in added if not e.get("status")]
    },ensure_ascii=False,indent=2)+"\n")
    print(f"facebookSources={len(sources)} raw={len(raw_records)} valid={len(candidates)} added={len(added)}")

if __name__=="__main__":
    main()
