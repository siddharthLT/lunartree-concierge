"""Per-visitor session picks and ICP search terms.

company_recs.json (built from scripts/, researched per company) maps a company
key to its top sessions per day and its search terms. Visitors whose company
isn't in there get a fallback built from the modalities they picked.
"""
import json
from functools import lru_cache
from pathlib import Path

from . import directory

RECS_DIR = Path(__file__).resolve().parent / 'recs'

MODALITY_LABEL = {
    'api': 'APIs', 'small': 'small molecules', 'mab': 'mAbs', 'bispecific': 'bispecifics', 'adc': 'ADCs',
    'protein': 'recombinant proteins', 'biosimilar': 'biosimilars', 'cell': 'cell therapy',
    'gene': 'gene therapy', 'editing': 'gene editing', 'radio': 'radiopharmaceuticals',
    'microbiome': 'microbiome', 'device': 'devices', 'digital': 'digital therapeutics',
}
GEO_LABEL = {'nam': 'North America', 'eu': 'Europe', 'apac': 'APAC', 'mea': 'MEA', 'anz': 'ANZ'}
STAGE_LABEL = {'discovery': 'discovery', 'preclinical': 'preclinical', 'phase1': 'Phase 1', 'phase2': 'Phase 2',
               'phase3': 'Phase 3', 'commercial': 'commercial-stage'}


@lru_cache(maxsize=1)
def _sessions():
    try:
        return json.loads((RECS_DIR / 'sessions.json').read_text())
    except (OSError, ValueError):
        return []


@lru_cache(maxsize=1)
def _company_recs():
    try:
        return json.loads((RECS_DIR / 'company_recs.json').read_text())
    except (OSError, ValueError):
        return {}


def _join(items, limit=3):
    items = list(items)[:limit]
    return ' / '.join(items)


def _fill(term, visitor):
    geo = _join((GEO_LABEL[g] for g in visitor.geographies if g in GEO_LABEL)) or 'US & EU'
    stage = _join((STAGE_LABEL[s] for s in visitor.phases if s in STAGE_LABEL)) or ''
    out = term.replace('{geo}', geo)
    out = out.replace('{stage} ', f'{stage} ' if stage else '').replace('{stage}', stage)
    return ' '.join(out.split())


def _fallback_sessions(visitor):
    mods = set(visitor.modalities)
    picks = {1: [], 2: []}
    scored = []
    for s in _sessions():
        if s['kind'] not in ('talk', 'roundtable') or s['day'] not in picks:
            continue
        overlap = mods & set(s['mods'])
        if overlap:
            scored.append((len(overlap), s, overlap))
    scored.sort(key=lambda t: -t[0])
    for _, s, overlap in scored:
        if len(picks[s['day']]) < 3:
            labels = ', '.join(MODALITY_LABEL[m] for m in sorted(overlap))
            picks[s['day']].append({**s, 'reason': f'Covers {labels} — the focus you picked.', 'meet': s['known_orgs']})
    return picks


def _fallback_terms(visitor):
    terms = []
    geo = '{geo}'
    stage = '{stage} '
    for m in visitor.modalities[:4]:
        terms.append(f'{stage}{MODALITY_LABEL.get(m, m)} biotechs in {geo} outsourcing CMC')
    if not terms:
        terms.append(f'{stage}biotechs in {geo} looking for a CDMO partner')
    return terms


def for_visitor(visitor):
    sessions = {s['id']: s for s in _sessions()}
    key = directory.company_key(visitor.directory_id, visitor.company)
    rec = _company_recs().get(key) if key else None

    if rec:
        picks = {1: [], 2: []}
        for day, items in ((1, rec.get('day1', [])), (2, rec.get('day2', []))):
            for it in items:
                s = sessions.get(it['id'])
                if s:
                    picks[day].append({**s, 'reason': it['reason'], 'meet': it.get('meet', [])})
        terms = rec.get('search_terms') or _fallback_terms(visitor)
    else:
        picks, terms = _fallback_sessions(visitor), _fallback_terms(visitor)

    for items in picks.values():
        items.sort(key=lambda s: tuple(int(x) for x in s['start'].split(':')))

    return {
        'personalised': bool(rec),
        'sessions': {str(d): v for d, v in picks.items()},
        'search_terms': [_fill(t, visitor) for t in terms],
        'dates': {'1': 'Tue 20 Oct', '2': 'Wed 21 Oct'},
    }
