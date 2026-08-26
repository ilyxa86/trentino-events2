#!/usr/bin/env python3
"""Enumerate known Trentino event calendars without curating results.

This job does not decide what is important and does not translate events. It only
proves how much of each source was traversed and exports raw candidate records for
the AI maintenance pass to parse, deduplicate and merge into events.json.
"""
from __future__ import annotations
import json,re,time
from datetime import date,datetime
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
S=requests.Session(); S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; TrentinoEventsCoverageBot/1.0; +https://ilyxa86.github.io/trentino-events2/)','Accept-Language':'it-IT,it;q=.9,en;q=.7,de;q=.6'})

def clean(x): return re.sub(r'\s+',' ',str(x or '')).strip()
def fetch(url):
 r=S.get(url,timeout=35,allow_redirects=True); r.raise_for_status(); return BeautifulSoup(r.text,'html.parser'),r.url,r.text

def base_audit(src):
 return {'priority':src.get('priority'),'lastScan':datetime.utcnow().replace(microsecond=0).isoformat()+'Z','status':'FAILED','reportedTotal':None,'recordsSeen':0,'uniqueCandidates':0,'pagesOrBucketsScanned':[],'attachmentsScanned':[],'errors':[],'notes':[]}

def reported_total(text):
 for pat in [r'([\d.]+)\s+risultati',r'\d+\s*-\s*\d+\s*/\s*([\d.]+)']:
  m=re.search(pat,text,re.I)
  if m:
   try:return int(m.group(1).replace('.',''))
   except: pass
 return None

def title_of(a):
 for tag in ['h1','h2','h3','h4','strong']:
  x=a.find(tag)
  if x and clean(x.get_text(' ',strip=True)): return clean(x.get_text(' ',strip=True))
 return clean(a.get_text(' ',strip=True))[:180]

def block_of(node):
 best=clean(node.get_text(' ',strip=True)); n=node
 for _ in range(5):
  n=getattr(n,'parent',None)
  if not n: break
  txt=clean(n.get_text(' ',strip=True))
  if len(best)<len(txt)<=900: best=txt
  if 40<=len(txt)<=650 and (re.search(r'20\d{2}',txt) or re.search(r'\d{1,2}[./-]\d{1,2}',txt)): return txt
 return best

def row(src,page_url,detail_url,title,text,image=''):
 return {'sourceId':src['id'],'sourceName':src['name'],'pageUrl':page_url,'detailUrl':detail_url,'title':clean(title),'rawText':clean(text)[:1400],'image':image,'enumeratedAt':datetime.utcnow().replace(microsecond=0).isoformat()+'Z'}

def dedupe(rows):
 d={}
 for r in rows:
  k=(r['sourceId'],r.get('detailUrl') or '',r.get('title') or '',r.get('rawText') or '')
  d[k]=r
 return list(d.values())

def page_rows(src,sp,page_url,href_filter=None):
 out=[]
 if href_filter:
  for a in sp.find_all('a',href=True):
   href=urljoin(page_url,a['href']).split('#')[0]
   if not href_filter(href): continue
   img=a.find('img'); image=urljoin(page_url,img.get('src') or img.get('data-src') or '') if img else ''
   out.append(row(src,page_url,href,title_of(a),block_of(a),image))
 else:
  for h in sp.find_all(['h2','h3','h4']):
   txt=block_of(h)
   if not (re.search(r'20\d{2}',txt) or re.search(r'\d{1,2}[./-]\d{1,2}',txt)): continue
   n=h; link=''; image=''
   for _ in range(5):
    if not n: break
    a=n if getattr(n,'name',None)=='a' else n.find('a',href=True)
    if a and not link: link=urljoin(page_url,a.get('href'))
    img=n.find('img') if hasattr(n,'find') else None
    if img and not image: image=urljoin(page_url,img.get('src') or img.get('data-src') or '')
    n=getattr(n,'parent',None)
   out.append(row(src,page_url,link,clean(h.get_text(' ',strip=True)),txt,image))
 return dedupe(out)

def rovereto_events(src):
 a=base_audit(src); rows=[]; seen=set()
 for p in range(1,61):
  u=src['url'] if p==1 else f"{src['url']}?lang=it&pno={p}"
  try:sp,final,_=fetch(u); a['pagesOrBucketsScanned'].append(final)
  except Exception as e:a['errors'].append(f'page {p}: {e}'); break
  rs=page_rows(src,sp,final,lambda h:'/vivi/eventi/' in h and h.rstrip('/')!=src['url'].rstrip('/'))
  fresh=[r for r in rs if r['detailUrl'] not in seen]
  for r in fresh: seen.add(r['detailUrl']); rows.append(r)
  forward=any(int(v)>p for x in sp.find_all('a',href=True) for v in parse_qs(urlparse(x['href']).query).get('pno',[]) if v.isdigit())
  if p>1 and not forward: break
  if p>1 and not fresh: break
  time.sleep(.1)
 a['recordsSeen']=len(seen); a['uniqueCandidates']=len(dedupe(rows)); a['status']='COMPLETE' if a['pagesOrBucketsScanned'] and not any(e.startswith('page ') for e in a['errors']) else 'PARTIAL'
 return dedupe(rows),a

def rovereto_estate(src):
 a=base_audit(src); rows=[]
 try:sp,final,_=fetch(src['url']); a['pagesOrBucketsScanned'].append(final)
 except Exception as e:a['errors'].append(str(e)); return [],a
 rows=page_rows(src,sp,final,lambda h:'/vivi/eventi/' in h)
 for x in sp.find_all('a',href=True):
  h=urljoin(final,x['href'])
  if re.search(r'\.(pdf|jpg|jpeg|png)(?:\?|$)',h,re.I):
   try:r=S.get(h,timeout=35); r.raise_for_status(); a['attachmentsScanned'].append({'url':h,'bytes':len(r.content),'contentType':r.headers.get('content-type','')})
   except Exception as e:a['errors'].append(f'attachment {h}: {e}')
 a['recordsSeen']=len(rows); a['uniqueCandidates']=len(rows); a['status']='COMPLETE' if a['pagesOrBucketsScanned'] and not a['errors'] else 'PARTIAL'
 return rows,a

def garda(src):
 a=base_audit(src); rows=[]; pages=None
 for p in range(1,101):
  u=src['url'] if p==1 else f"{src['url']}?page={p}"
  try:sp,final,_=fetch(u); txt=clean(sp.get_text(' ',strip=True)); a['pagesOrBucketsScanned'].append(final)
  except Exception as e:a['errors'].append(f'page {p}: {e}'); break
  tot=reported_total(txt)
  if tot: a['reportedTotal']=max(a['reportedTotal'] or 0,tot); pages=(tot+8)//9
  before=len(rows); rows.extend(page_rows(src,sp,final)); rows=dedupe(rows)
  if pages and p>=pages: break
  if p>1 and len(rows)==before: break
 a['recordsSeen']=len(rows); a['uniqueCandidates']=len(rows); a['status']='COMPLETE' if pages and len(a['pagesOrBucketsScanned'])>=pages and not any(e.startswith('page ') for e in a['errors']) else 'PARTIAL'
 return rows,a

def sitemap_event_urls(base,patterns,a):
 q=urlparse(base); root=f'{q.scheme}://{q.netloc}'; todo=[root+'/sitemap.xml',root+'/sitemap_index.xml']; seen=set(); urls=set()
 try:
  r=S.get(root+'/robots.txt',timeout=20)
  for line in r.text.splitlines():
   if line.lower().startswith('sitemap:'): todo.append(line.split(':',1)[1].strip())
 except: pass
 while todo and len(seen)<100:
  u=todo.pop(0)
  if u in seen: continue
  seen.add(u)
  try:r=S.get(u,timeout=35); r.raise_for_status(); sp=BeautifulSoup(r.text,'xml')
  except Exception as e:a['errors'].append(f'sitemap {u}: {e}'); continue
  for x in sp.find_all('loc'):
   v=clean(x.get_text())
   if v.lower().endswith('.xml') or 'sitemap' in urlparse(v).path.lower(): todo.append(v)
   elif any(re.search(p,v,re.I) for p in patterns): urls.add(v)
 a['notes'].append(f'sitemaps={len(seen)}, matchingEventUrls={len(urls)}')
 return sorted(urls)

def visittrentino(src):
 a=base_audit(src); rows=[]
 try:sp,final,_=fetch(src['url']); txt=clean(sp.get_text(' ',strip=True)); a['pagesOrBucketsScanned'].append(final); a['reportedTotal']=reported_total(txt); rows.extend(page_rows(src,sp,final))
 except Exception as e:a['errors'].append(f'index: {e}'); return [],a
 urls=sitemap_event_urls(src['url'],[r'/guida/cosa-fare/eventi/.+_e_\d+'],a)
 for u in urls: rows.append(row(src,src['url'],u,'',''))
 rows=dedupe(rows); a['recordsSeen']=len(urls); a['uniqueCandidates']=len(rows)
 a['status']='COMPLETE' if a['reportedTotal'] and len(urls)>=a['reportedTotal'] else 'PARTIAL'
 if a['status']!='COMPLETE': a['notes'].append(f"reported={a['reportedTotal']}, sitemapEventUrls={len(urls)}; AI pass must resolve the gap")
 return rows,a

def generic(src):
 a=base_audit(src)
 try:sp,final,_=fetch(src['url']); a['pagesOrBucketsScanned'].append(final); rows=page_rows(src,sp,final); a['reportedTotal']=reported_total(clean(sp.get_text(' ',strip=True))); a['recordsSeen']=len(rows); a['uniqueCandidates']=len(rows); a['status']='PARTIAL'; a['notes'].append('Generic adapter enumerated visible candidates but cannot yet prove full pagination/date traversal.'); return rows,a
 except Exception as e:a['errors'].append(str(e)); return [],a

def main():
 reg=json.loads((DATA/'source_registry.json').read_text()); audit_path=DATA/'source_audit.json'; audit=json.loads(audit_path.read_text()) if audit_path.exists() else {'sources':{}}; rows=[]
 adapters={'visitrovereto_events':rovereto_events,'visitrovereto_estate':rovereto_estate,'garda_trentino_events':garda,'visittrentino_all_events':visittrentino}
 for src in reg.get('mandatorySources',[]):
  print(f"== {src['id']} ==",flush=True); fn=adapters.get(src['id'],generic)
  try:rs,a=fn(src)
  except Exception as e:a=base_audit(src); a['errors'].append(f'fatal: {e}'); rs=[]
  rows.extend(rs); audit.setdefault('sources',{})[src['id']]=a; print(json.dumps({'status':a['status'],'reportedTotal':a['reportedTotal'],'recordsSeen':a['recordsSeen'],'rows':len(rs),'pages':len(a['pagesOrBucketsScanned']),'errors':len(a['errors'])},ensure_ascii=False))
 rows=dedupe(rows); p0={s['id']:audit['sources'].get(s['id'],{}).get('status','NOT_SCANNED') for s in reg.get('mandatorySources',[]) if s.get('priority')=='P0'}
 audit.update({'protocolVersion':reg.get('version',2),'lastRun':datetime.utcnow().replace(microsecond=0).isoformat()+'Z','coverageWindow':{'from':date.today().isoformat(),'semantics':'rolling-12-month-overlap; raw enumerator may include out-of-window rows for AI resolution'},'overallStatus':'COMPLETE' if p0 and all(v=='COMPLETE' for v in p0.values()) else 'PARTIAL','p0Status':p0,'summary':{'rawCandidates':len(rows)},'note':'This deterministic enumerator feeds the AI maintenance pass. PARTIAL means the system must not claim complete coverage.'})
 (DATA/'discovered_candidates.json').write_text(json.dumps({'generatedAt':datetime.utcnow().replace(microsecond=0).isoformat()+'Z','records':rows},ensure_ascii=False,indent=2)+'\n'); audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n'); print(f"raw candidates={len(rows)} overall={audit['overallStatus']}")
if __name__=='__main__': main()
