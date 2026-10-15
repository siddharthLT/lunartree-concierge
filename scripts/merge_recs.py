"""Merge scripts/rec_batches/out_*.json into concierge/recs/company_recs.json,
dropping anything that fails validation and reporting what was dropped."""
import glob, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sessions = {s['id']: s for s in json.loads((ROOT / 'concierge/recs/sessions.json').read_text())}
companies = json.loads((ROOT / 'concierge/data/cdmo_live_directory.json').read_text())['companies']

def to_min(t):
    h, m = t.strip().split(':'); return int(h) * 60 + int(m)

import re

ALIASES = {'eli lilly and company': 'Eli Lilly', 'eli lilly & co': 'Eli Lilly', 'eli lilly & co.': 'Eli Lilly',
           'the brookings institution': 'The Brookings Institution'}

def clean_org(o):
    return ALIASES.get(o.strip().lower(), o.strip())

def clean_reason(r):
    # internal hedges from the research pass must not reach visitors
    r = re.sub(r'\s*[\(\[]?\s*(title[- ]only( listed)?|only (the )?title (is )?(listed|known))\s*[\)\]]?[.,;:]?', '', r, flags=re.I)
    r = re.sub(r'(?<=[.;])\s*[^.;]*(unverified|chosen from titles|guess)[^.;]*[.;]?', '', r, flags=re.I)
    return re.sub(r'\s+', ' ', r).strip()

merged, problems = {}, []
for f in sorted(glob.glob(str(ROOT / 'scripts/rec_batches/out_*.json'))):
    merged.update(json.loads(Path(f).read_text()))

out = {}
for key, rec in merged.items():
    if key not in companies:
        problems.append(f'{key}: unknown company'); continue
    clean = {'search_terms': [t.strip() for t in rec.get('search_terms', []) if t.strip()][:5]}
    if len(clean['search_terms']) < 4:
        problems.append(f'{key}: only {len(clean["search_terms"])} search terms')
    for day in (1, 2):
        picked = []
        for it in rec.get(f'day{day}', []):
            s = sessions.get(it.get('id'))
            if not s or s['day'] != day or s['kind'] not in ('talk', 'roundtable'):
                problems.append(f'{key}: bad session {it.get("id")} for day{day}'); continue
            clash = [p for p in picked if to_min(s['start']) < to_min(sessions[p['id']]['end']) and to_min(sessions[p['id']]['start']) < to_min(s['end'])]
            if clash:
                problems.append(f'{key}: {s["id"]} overlaps {clash[0]["id"]} — dropped'); continue
            it['reason'] = clean_reason(it.get('reason', ''))
            if len(it['reason']) < 40:
                problems.append(f'{key}: weak reason for {s["id"]}'); continue
            picked.append({'id': s['id'], 'reason': it['reason'].strip(), 'meet': list(dict.fromkeys(clean_org(m) for m in it.get('meet', []) if m))[:3]})
        clean[f'day{day}'] = picked[:3]
        if len(picked) < 2:
            problems.append(f'{key}: only {len(picked)} valid picks on day {day}')
    out[key] = clean

(ROOT / 'concierge/recs/company_recs.json').write_text(json.dumps(out, indent=1))
missing = [k for k in companies if k and k not in out]
print(f'{len(out)} companies merged; missing: {missing}')
print(f'{len(problems)} issues'); [print(' -', p) for p in problems[:60]]
