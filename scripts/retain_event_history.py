#!/usr/bin/env python3
"""Retain all ongoing/future events and the 100 most recently ended events."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LIMIT = 100
ROOT = Path(__file__).resolve().parents[1]

def retain_history(events, today):
    # Unknown dates are preserved rather than accidentally removing live events.
    historical = [e for e in events if e.get('endDate') and e['endDate'] < today]
    historical.sort(key=lambda e: (e['endDate'], e.get('startDate') or '', e.get('id') or ''), reverse=True)
    retained = {id(e) for e in historical[:LIMIT]}
    return [e for e in events if not e.get('endDate') or e['endDate'] >= today or id(e) in retained]

def main():
    path = ROOT / 'data/events.json'
    events = json.loads(path.read_text(encoding='utf-8'))
    today = datetime.now(ZoneInfo('Europe/Rome')).date().isoformat()
    kept = retain_history(events, today)
    if len(kept) != len(events):
        path.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'History limited to {LIMIT}: removed={len(events)-len(kept)}, total={len(kept)}')

if __name__ == '__main__':
    main()
