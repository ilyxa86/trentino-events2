#!/usr/bin/env python3
"""Deterministically enumerate known Trentino event sources.

This layer is deliberately non-curatorial: it traverses source indexes, pagination,
sitemaps and programme pages and produces raw candidates plus a coverage audit.
The AI maintenance pass resolves details, recurrence, translations and deduplication.
"""
from __future__ import annotations
import json,re,time
from datetime import date,datetime
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
S=requests.Session(); S.headers.update({'User-Agent':'Mozilla/5.0 (compatible; TrentinoEventsCoverageBot/2.0; +https://ilyxa86.github.io/trentino-events2/)','Accept-Language':'it-IT,it;q=.9,en;q=.7,de;q=.6'})
GENERIC_SKIP={'top','image','events','eventi','agenda','next >','successivo','precedente','other available dates','altre date disponibili'}

def now(): return datetime.utcnow().replace(microsecond=0).isoformat()+'Z'
def clean(x): return re.sub(r'\s+',' ',str(x or '')).strip()
def fetch(url):
 r=S.get(url,timeout=35,allow_redirects=True); r.raise_for_status(); return BeautifulSoup(r.text,'html.parser'),r.url,r.text

def base_audit(src):
 return {'priority':src.get('priority'),'lastScan':now(),'status':'FAILED','reportedTotal':None,'recordsSeen':0,'uniqueCandidates':0,'pagesOrBucketsScanned':[],'attachmentsScanned':[],'errors':[],'notes':[]}

def reported_total(text):
 for pat in [r'trovati\s+([\d.]+)\s+risultati',r'([\d.]+)\s+risultati(?:\s+trovati)?',r'\d+\s*-\s*\d+\s*/\s*([\d.]+)']:
  m=re.search(pat,text,re.I)
  if m:
   try:return int(m.group(1).replace('.',''))
   except: pass
 return None

def title_of(a):
 for tag in ['h1','h2','h3','h4','h5','strong']:
  x=a.find(tag)
  if x and clean(x.get_text(' ',strip=True)): return clean(x.get_text(' ',strip=True))
 t=clean(a.get_text(' ',strip=True)); return t[:200]

def block_of(node,maxlen=1200):
 best=clean(node.get_text(' ',strip=True)); n=node
 for _ in range(7):
  n=getattr(n,'parent',None)
  if not n: break
  txt=clean(n.get_text(' ',strip=True))
  if len(best)<len(txt)<=maxlen: best=txt
  if 35<=len(txt)<=750 and (re.search(r'20\d{2}',txt) or re.search(r'\d{1,2}[./-]\d{1,2}',txt)): return txt
 return best

def row(src,page_url,detail_url,title,text,image=''):
 return {'sourceId':src['id'],'sourceName':src['name'],'pageUrl':page_url,'detailUrl':detail_url,'title':clean(title),'rawText':clean(text)[:1600],'image':image,'enumeratedAt':now()}

def dedupe(rows):
 d={}
 for r in rows:
  k=(r['sourceId'],r.get('detailUrl') or '',r.get('title') or '',r.get('rawText') or '')
  d[k]=r
 return list(d.values())

def unique_urls(rows): return {r.get('detailUrl') for r in rows if r.get('detailUrl')}

def page_rows(src,sp,page_url,href_filter=None):
 out=[]
 if href_filter:
  for a in sp.find_all('a',href=True):
   href=urljoin(page_url,a['href']).split('#')[0]
   if not href_filter(href): continue
   img=a.find('img'); image=urljoin(page_url,img.get('src') or img.get('data-src') or '') if img else ''
   out.append(row(src,page_url,href,title_of(a),block_of(a),image))
 else:
  for h in sp.find_all(['h2','h3','h4','h5']):
   txt=block_of(h)
   if not (re.search(r'20\d{2}',txt) or re.search(r'\d{1,2}[./-]\d{1,2}',txt)): continue
   n=h; link=''; image=''
   for _ in range(6):
    if not n: break
    a=n if getattr(n,'name',None)=='a' else n.find('a',href=True)
    if a and not link: link=urljoin(page_url,a.get('href'))
    img=n.find('img') if hasattr(n,'find') else None
    if img and not image: image=urljoin(page_url,img.get('src') or img.get('data-src') or '')
    n=getattr(n,'parent',None)
   out.append(row(src,page_url,link,clean(h.get_text(' ',strip=True)),txt,image))
 return dedupe(out)

def text_date_rows(src,sp,page_url):
 """Fallback for JS-ish listings whose event cards have text but no usable links/headings."""
 vals=[clean(x) for x in sp.stripped_strings if clean(x)]
 date_re=re.compile(r'(?:(?:\d{1,2}[./]\d{1,2})(?:\s*-\s*\d{1,2}[./]\d{1,2})?[./]?\s*20\d{2})')
 out=[]
 for i,v in enumerate(vals):
  if not date_re.search(v): continue
  title=''
  for j in range(i-1,max(-1,i-7),-1):
   cand=vals[j]
   if cand.lower() in GENERIC_SKIP or len(cand)<3 or len(cand)>220: continue
   if date_re.search(cand) or re.fullmatch(r'\d+[-/]\d+\s*/\s*\d+',cand): continue
   title=cand; break
  if not title: continue
  tail=[]
  for x in vals[i:min(len(vals),i+6)]:
   if len(' '.join(tail))>500: break
   tail.append(x)
  out.append(row(src,page_url,'',title,' | '.join([title]+tail)))
 return dedupe(out)

def sitemap_event_urls(base,patterns,a,max_sitemaps=160):
 q=urlparse(base); root=f'{q.scheme}://{q.netloc}'; todo=[root+'/sitemap.xml',root+'/sitemap_index.xml']; seen=set(); urls=set()
 try:
  r=S.get(root+'/robots.txt',timeout=20)
  for line in r.text.splitlines():
   if line.lower().startswith('sitemap:'): todo.append(line.split(':',1)[1].strip())
 except Exception as e:a['notes'].append(f'robots unavailable: {e}')
 while todo and len(seen)<max_sitemaps:
  u=todo.pop(0)
  if u in seen: continue
  seen.add(u)
  try:r=S.get(u,timeout=35); r.raise_for_status(); sp=BeautifulSoup(r.text,'xml')
  except Exception as e:
   if not u.endswith('/sitemap_index.xml'): a['errors'].append(f'sitemap {u}: {e}')
   continue
  for x in sp.find_all('loc'):
   v=clean(x.get_text())
   if v.lower().endswith('.xml') or 'sitemap' in urlparse(v).path.lower(): todo.append(v)
   elif any(re.search(p,v,re.I) for p in patterns): urls.add(v)
 a['notes'].append(f'sitemaps={len(seen)}, matchingEventUrls={len(urls)}')
 return sorted(urls)

def rovereto_events(src):
 a=base_audit(src); rows=[]; seen=set(); ended=False
 for p in range(1,81):
  u=src['url'] if p==1 else f"{src['url']}?lang=it&pno={p}"
  try:sp,final,_=fetch(u); a['pagesOrBucketsScanned'].append(final)
  except Exception as e:a['errors'].append(f'page {p}: {e}'); break
  rs=page_rows(src,sp,final,lambda h:'/vivi/eventi/' in h and h.rstrip('/')!=src['url'].rstrip('/'))
  fresh=[r for r in rs if r['detailUrl'] not in seen]
  for r in fresh: seen.add(r['detailUrl']); rows.append(r)
  forward=any(int(v)>p for x in sp.find_all('a',href=True) for v in parse_qs(urlparse(x['href']).query).get('pno',[]) if v.isdigit())
  if p>1 and not forward: ended=True; break
  if p>1 and not fresh: ended=True; break
  time.sleep(.05)
 a['recordsSeen']=len(seen); a['uniqueCandidates']=len(dedupe(rows)); a['status']='COMPLETE' if ended and not a['errors'] else 'PARTIAL'
 return dedupe(rows),a

def rovereto_estate(src):
 a=base_audit(src)
 try:sp,final,_=fetch(src['url']); a['pagesOrBucketsScanned'].append(final)
 except Exception as e:a['errors'].append(str(e)); return [],a
 rows=page_rows(src,sp,final,lambda h:'/vivi/eventi/' in h)
 pdf_count=0
 for x in sp.find_all('a',href=True):
  h=urljoin(final,x['href'])
  if re.search(r'\.pdf(?:\?|$)',h,re.I):
   try:r=S.get(h,timeout=45); r.raise_for_status(); a['attachmentsScanned'].append({'url':h,'bytes':len(r.content),'contentType':r.headers.get('content-type',''),'inspection':'downloaded_for_AI_attachment_review'}); pdf_count+=1
   except Exception as e:a['errors'].append(f'attachment {h}: {e}')
 a['recordsSeen']=len(rows); a['uniqueCandidates']=len(rows)
 # Download proves availability, not semantic PDF extraction; keep PARTIAL so AI must inspect it.
 a['status']='PARTIAL' if pdf_count else ('COMPLETE' if not a['errors'] else 'PARTIAL')
 if pdf_count:a['notes'].append('Linked programme PDF downloaded but semantic contents must be reconciled by the AI pass before source can be COMPLETE.')
 return rows,a

def garda(src):
 a=base_audit(src); rows=[]; pages=1; raw_seen=0
 for p in range(1,101):
  u=src['url'] if p==1 else f"{src['url']}?page={p}"
  try:sp,final,_=fetch(u); txt=clean(sp.get_text(' ',strip=True)); a['pagesOrBucketsScanned'].append(final)
  except Exception as e:a['errors'].append(f'page {p}: {e}'); break
  tot=reported_total(txt)
  if tot:
   a['reportedTotal']=max(a['reportedTotal'] or 0,tot); pages=max(pages,(a['reportedTotal']+8)//9)
  rs=text_date_rows(src,sp,final); raw_seen+=len(rs); rows.extend(rs); rows=dedupe(rows)
  if p>=pages and a['reportedTotal']: break
  time.sleep(.05)
 a['recordsSeen']=raw_seen; a['uniqueCandidates']=len(rows)
 a['status']='COMPLETE' if a['reportedTotal'] and len(a['pagesOrBucketsScanned'])>=pages and raw_seen>=a['reportedTotal'] and not a['errors'] else 'PARTIAL'
 if a['status']!='COMPLETE': a['notes'].append(f"Garda reconciliation: reported={a['reportedTotal']} recordsSeenAcrossPages={raw_seen} uniqueCandidates={len(rows)} expectedPages={pages}")
 return rows,a

def visittrentino(src):
 a=base_audit(src); rows=[]
 try:sp,final,_=fetch(src['url']); txt=clean(sp.get_text(' ',strip=True)); a['pagesOrBucketsScanned'].append(final); a['reportedTotal']=reported_total(txt); rows.extend(page_rows(src,sp,final))
 except Exception as e:a['errors'].append(f'index: {e}'); return [],a
 urls=sitemap_event_urls(src['url'],[r'/guida/cosa-fare/eventi/.+_e_\d+'],a)
 for u in urls: rows.append(row(src,src['url'],u,'',''))
 rows=dedupe(rows); a['recordsSeen']=len(urls); a['uniqueCandidates']=len(rows)
 # A sitemap superset larger than the live result total is valuable discovery but is not count reconciliation.
 a['status']='COMPLETE' if a['reportedTotal'] and len(urls)==a['reportedTotal'] else 'PARTIAL'
 if a['status']!='COMPLETE': a['notes'].append(f"Live index reports {a['reportedTotal']}; sitemap exposes {len(urls)} event URLs. AI/date filtering must reconcile the live 12-month set.")
 return rows,a

def opencontent_agenda(src):
 """Enumerate OpenContent/OpenAgenda city calendars via search pages or sitemap."""
 a=base_audit(src); rows=[]; root=f"{urlparse(src['url']).scheme}://{urlparse(src['url']).netloc}"
 is_rovereto='rovereto' in root
 pattern=(r'/agenda/event/\d+$' if is_rovereto else r'/Eventi/[^/?#]+$')
 search0=root+'/content/search/?Order=desc'
 try:sp,final,_=fetch(search0); txt=clean(sp.get_text(' ',strip=True)); a['pagesOrBucketsScanned'].append(final); total=reported_total(txt); a['reportedTotal']=total
 except Exception as e:
  a['errors'].append(f'search index: {e}'); sp=None; total=None
 if sp is not None:
  filt=lambda h: bool(re.search(pattern,urlparse(h).path,re.I))
  rows.extend(page_rows(src,sp,final,filt))
  if total:
   pages=(total+19)//20
   for offset in range(20,pages*20,20):
    u=f'{root}/content/search/%28offset%29/{offset}?Order=desc'
    try:p,fin,_=fetch(u); a['pagesOrBucketsScanned'].append(fin); rows.extend(page_rows(src,p,fin,filt))
    except Exception as e:a['errors'].append(f'offset {offset}: {e}'); break
    time.sleep(.035)
 # Sitemap is a second enumeration path and catches event pages not exposed by search ordering.
 urls=sitemap_event_urls(root,[pattern],a,80)
 for u in urls: rows.append(row(src,src['url'],u,'',''))
 rows=dedupe(rows); unique=len(unique_urls(rows)); a['recordsSeen']=unique; a['uniqueCandidates']=len(rows)
 if total:
  expected=(total+19)//20
  scanned_search=sum('/content/search' in x for x in a['pagesOrBucketsScanned'])
  a['status']='COMPLETE' if scanned_search>=expected and unique>=total and not any('offset ' in e for e in a['errors']) else 'PARTIAL'
  if a['status']!='COMPLETE':a['notes'].append(f'OpenAgenda reconciliation: reported={total} uniqueEventUrls={unique} searchPages={scanned_search}/{expected}')
 else:
  # No count means sitemap gives broad deterministic discovery but no count proof.
  a['status']='PARTIAL'; a['notes'].append(f'No source-reported total available; discovered {unique} unique event URLs via search/sitemap.')
 return rows,a

def cultura_rassegne(src):
 a=base_audit(src); rows=[]; seen=set(); series=[]; ended=False
 filt=lambda h:'/Rassegne/' in urlparse(h).path and '/Rassegne-concluse' not in h and h.rstrip('/')!=src['url'].rstrip('/')
 for off in range(0,240,12):
  u=src['url'] if off==0 else f"{src['url']}/%28offset%29/{off}"
  try:sp,final,_=fetch(u); a['pagesOrBucketsScanned'].append(final)
  except Exception as e:a['errors'].append(f'offset {off}: {e}'); break
  rs=page_rows(src,sp,final,filt); fresh=[r for r in rs if r['detailUrl'] not in seen]
  for r in fresh: seen.add(r['detailUrl']); rows.append(r); series.append(r['detailUrl'])
  if off>0 and not fresh: ended=True; break
  time.sleep(.04)
 # Every active series page may contain separately linked programme events.
 child_seen=set()
 for u in series:
  try:sp,final,_=fetch(u); a['pagesOrBucketsScanned'].append(final+'#children')
  except Exception as e:a['errors'].append(f'series {u}: {e}'); continue
  cr=page_rows(src,sp,final,lambda h:'/Appuntamenti/' in urlparse(h).path and '{{' not in h)
  for r in cr:
   if r['detailUrl'] not in child_seen: child_seen.add(r['detailUrl']); rows.append(r)
  for x in sp.find_all('a',href=True):
   h=urljoin(final,x['href'])
   if re.search(r'\.pdf(?:\?|$)',h,re.I) and h not in {z.get('url') for z in a['attachmentsScanned']}:
    a['attachmentsScanned'].append({'url':h,'inspection':'AI_review_required'})
 rows=dedupe(rows); a['recordsSeen']=len(seen)+len(child_seen); a['uniqueCandidates']=len(rows)
 a['status']='COMPLETE' if ended and not a['errors'] else 'PARTIAL'
 if a['attachmentsScanned']:
  a['status']='PARTIAL'; a['notes'].append('Series PDF attachments require AI semantic inspection before completeness can be asserted.')
 a['notes'].append(f'activeSeries={len(seen)} linkedProgrammeEvents={len(child_seen)}')
 return rows,a

def cultura_appuntamenti(src):
 """Broad deterministic URL discovery; dynamic calendar reconciliation remains an AI gap-closing task."""
 a=base_audit(src); rows=[]
 try:sp,final,_=fetch(src['url']); a['pagesOrBucketsScanned'].append(final); a['reportedTotal']=reported_total(clean(sp.get_text(' ',strip=True))); rows.extend(page_rows(src,sp,final))
 except Exception as e:a['errors'].append(f'calendar index: {e}')
 urls=sitemap_event_urls(src['url'],[r'/Appuntamenti/[^/?#{}]+$'],a,120)
 # Limit raw feed to public event URLs whose sitemap path is real; AI can use source audit to close date-specific gaps.
 for u in urls: rows.append(row(src,src['url'],u,'',''))
 rows=dedupe(rows); a['recordsSeen']=len(urls); a['uniqueCandidates']=len(rows); a['status']='PARTIAL'
 a['notes'].append(f'Dynamic date calendar cannot yet be count-reconciled deterministically; {len(urls)} Appuntamenti URLs discovered via sitemap. AI pass must traverse date buckets/close gaps.')
 return rows,a

def generic(src):
 a=base_audit(src)
 try:sp,final,_=fetch(src['url']); a['pagesOrBucketsScanned'].append(final); rows=page_rows(src,sp,final); a['reportedTotal']=reported_total(clean(sp.get_text(' ',strip=True))); a['recordsSeen']=len(rows); a['uniqueCandidates']=len(rows); a['status']='PARTIAL'; a['notes'].append('Generic adapter enumerated visible candidates but cannot prove full pagination/date traversal.'); return rows,a
 except Exception as e:a['errors'].append(str(e)); return [],a

def main():
 reg=json.loads((DATA/'source_registry.json').read_text()); audit_path=DATA/'source_audit.json'; audit=json.loads(audit_path.read_text()) if audit_path.exists() else {'sources':{}}; rows=[]
 adapters={'visitrovereto_events':rovereto_events,'visitrovereto_estate':rovereto_estate,'garda_trentino_events':garda,'visittrentino_all_events':visittrentino,'comune_rovereto_events':opencontent_agenda,'comune_trento_events':opencontent_agenda,'trentino_cultura_rassegne':cultura_rassegne,'trentino_cultura_appuntamenti':cultura_appuntamenti}
 for src in reg.get('mandatorySources',[]):
  print(f"== {src['id']} ==",flush=True); fn=adapters.get(src['id'],generic)
  try:rs,a=fn(src)
  except Exception as e:a=base_audit(src); a['errors'].append(f'fatal: {e}'); rs=[]
  rows.extend(rs); audit.setdefault('sources',{})[src['id']]=a
  print(json.dumps({'status':a['status'],'reportedTotal':a['reportedTotal'],'recordsSeen':a['recordsSeen'],'rows':len(rs),'pages':len(a['pagesOrBucketsScanned']),'errors':len(a['errors'])},ensure_ascii=False),flush=True)
 rows=dedupe(rows); p0={s['id']:audit['sources'].get(s['id'],{}).get('status','NOT_SCANNED') for s in reg.get('mandatorySources',[]) if s.get('priority')=='P0'}
 audit.update({'protocolVersion':reg.get('version',2),'lastRun':now(),'coverageWindow':{'from':date.today().isoformat(),'semantics':'rolling-12-month-overlap; raw enumerator may include out-of-window rows for AI resolution'},'overallStatus':'COMPLETE' if p0 and all(v=='COMPLETE' for v in p0.values()) else 'PARTIAL','p0Status':p0,'summary':{'rawCandidates':len(rows)},'note':'Deterministic enumeration feeds the AI maintenance pass. PARTIAL means the system must not claim complete coverage.'})
 (DATA/'discovered_candidates.json').write_text(json.dumps({'generatedAt':now(),'records':rows},ensure_ascii=False,indent=2)+'\n'); audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n'); print(f"raw candidates={len(rows)} overall={audit['overallStatus']}")
if __name__=='__main__': main()
