#!/usr/bin/env python3
"""Normalize crawler output and compute stable raw-source deltas.

The enumerator intentionally produces a full snapshot. This post-pass removes
run timestamps from individual records, adds stable candidate IDs/fingerprints,
and compares the new snapshot with the version at Git HEAD. A MISSING raw
candidate is emitted only when both the previous and current audit say that
source was COMPLETE, preventing false removals from partial scans.
"""
from __future__ import annotations
import hashlib,json,re,subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'

def clean(v): return re.sub(r'\s+',' ',str(v or '')).strip()
def norm(v): return clean(v).casefold()
def sha(v): return hashlib.sha256(v.encode('utf-8')).hexdigest()[:24]

def canonical_url(url):
    url=clean(url)
    if not url: return ''
    try:
        s=urlsplit(url)
        # Remove common tracking params but preserve source pagination/event IDs.
        qs=[(k,v) for k,v in parse_qsl(s.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid'}]
        path=re.sub(r'/+$','',s.path) or '/'
        return urlunsplit((s.scheme.lower(),s.netloc.lower(),path,urlencode(qs,doseq=True),''))
    except Exception:
        return url

def date_tokens(text):
    vals=re.findall(r'(?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}(?:[-/.]20\d{2})?)',text or '')
    return '|'.join(vals[:6])

def identity_payload(r):
    sid=norm(r.get('sourceId'))
    detail=canonical_url(r.get('detailUrl'))
    if detail:
        return f'{sid}|url|{detail}'
    title=norm(r.get('title'))
    dates=date_tokens(clean(r.get('rawText')))
    # Raw-text prefix helps distinguish identically titled recurring cards while
    # keeping the key reasonably stable when descriptions change later.
    prefix=norm(r.get('rawText'))[:220]
    return f'{sid}|text|{title}|{dates}|{prefix}'

def signature_payload(r):
    return '|'.join([
        norm(r.get('sourceId')),
        canonical_url(r.get('pageUrl')),
        canonical_url(r.get('detailUrl')),
        norm(r.get('title')),
        norm(r.get('rawText')),
        canonical_url(r.get('image')),
    ])

def normalize_record(r):
    x={k:v for k,v in r.items() if k not in {'enumeratedAt','candidateKey','candidateSignature'}}
    x['pageUrl']=canonical_url(x.get('pageUrl'))
    x['detailUrl']=canonical_url(x.get('detailUrl'))
    x['image']=canonical_url(x.get('image'))
    x['title']=clean(x.get('title'))
    x['rawText']=clean(x.get('rawText'))
    x['candidateKey']=sha(identity_payload(x))
    x['candidateSignature']=sha(signature_payload(x))
    return x

def git_json(path,default):
    try:
        raw=subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL)
        return json.loads(raw)
    except Exception:
        return default

def complete_sources(audit):
    return {sid for sid,item in (audit.get('sources') or {}).items() if item.get('status')=='COMPLETE'}

def main():
    current_path=DATA/'discovered_candidates.json'
    audit_path=DATA/'source_audit.json'
    current=json.loads(current_path.read_text()) if current_path.exists() else {'records':[]}
    current_audit=json.loads(audit_path.read_text()) if audit_path.exists() else {'sources':{}}
    previous=git_json('data/discovered_candidates.json',{'records':[]})
    previous_audit=git_json('data/source_audit.json',{'sources':{}})

    cur_records=[normalize_record(r) for r in current.get('records',[])]
    prev_records=[normalize_record(r) for r in previous.get('records',[])]
    # Prefer the last occurrence if a source accidentally produced duplicate identities.
    cur={r['candidateKey']:r for r in cur_records}
    prev={r['candidateKey']:r for r in prev_records}

    delta=[]
    for key,r in cur.items():
        old=prev.get(key)
        if old is None:
            delta.append({'change':'ADDED','candidate':r})
        elif old.get('candidateSignature')!=r.get('candidateSignature'):
            delta.append({'change':'CHANGED','candidate':r,'previousSignature':old.get('candidateSignature')})

    safe_missing=complete_sources(current_audit)&complete_sources(previous_audit)
    for key,r in prev.items():
        if key not in cur and r.get('sourceId') in safe_missing:
            delta.append({'change':'MISSING','candidate':r})

    # Stable ordering makes reviews and diffs useful.
    records=sorted(cur.values(),key=lambda r:(r.get('sourceId',''),r.get('candidateKey','')))
    delta=sorted(delta,key=lambda d:(d.get('candidate',{}).get('sourceId',''),d.get('change',''),d.get('candidate',{}).get('candidateKey','')))
    generated=datetime.utcnow().replace(microsecond=0).isoformat()+'Z'
    current_path.write_text(json.dumps({'generatedAt':generated,'records':records},ensure_ascii=False,indent=2)+'\n')
    (DATA/'discovery_delta.json').write_text(json.dumps({
        'generatedAt':generated,
        'counts':{
            'ADDED':sum(1 for d in delta if d['change']=='ADDED'),
            'CHANGED':sum(1 for d in delta if d['change']=='CHANGED'),
            'MISSING':sum(1 for d in delta if d['change']=='MISSING'),
            'TOTAL':len(delta)
        },
        'missingSafety':'MISSING is emitted only when both previous and current source audits were COMPLETE.',
        'changes':delta
    },ensure_ascii=False,indent=2)+'\n')
    print(f'normalizedCandidates={len(records)} rawDelta={len(delta)} safeMissingSources={len(safe_missing)}')

if __name__=='__main__': main()
