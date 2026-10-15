"""CDMO_Live_Americas_2026_Sessions.csv -> concierge/recs/sessions.json

The CSV has no dates, descriptions or speakers, so day is inferred from row
order (the export lists Welcome Reception, then Day 1, then Day 2 starting with
the 06:15 run club) and `known_orgs` comes from the public agenda page
(pharmasource.global/cdmo-live-americas-agenda) track listings — track-level,
not confirmed per session.
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / 'CDMO_Live_Americas_2026_Sessions.csv', encoding='utf-8-sig')))

DAY0_END, DAY2_START = 0, 27  # row indexes: 0 = Welcome Reception (19 Oct), 27 = Running Club (21 Oct)
DATES = {0: ('Mon 19 Oct', 'Day Zero'), 1: ('Tue 20 Oct', 'Day 1'), 2: ('Wed 21 Oct', 'Day 2')}

KNOWN_ORGS = {  # session id -> orgs named for that topic on the agenda page
    '320117': ['The Brookings Institution', 'PBOA'],
    '320119': ['The Brookings Institution', 'PBOA'],
    '320118': ['Crescent Biopharma', 'Oliyai Consulting', 'Axplora'],
    '320122': ['Biogen', 'Eli Lilly', 'Astellas', 'Pfizer', 'Vertex'],
    '320135': ['Vertex'],
    '320136': ['Almac'],
    '320121': ['FDA', 'Eli Lilly', 'Bimeda'],
    '320124': ['Sanofi', 'Pfizer', 'Aizon', 'MasterControl'],
    '320145': ['Sanofi', 'Pfizer', 'Aizon', 'MasterControl'],
    '320138': ['AstraZeneca', 'Vertex'],
    '320140': ['AstraZeneca', 'Vertex', 'Gates MRI', 'QurAlis', 'Genetix Biotherapeutics'],
    '320127': ['AstraZeneca', 'Vertex', 'QurAlis'],
    '320141': ['APIIC'],
    '320143': ['PSCI'],
    '320142': [],
}

MODS = {  # session id -> modalities the topic speaks to (used only for the no-company-match fallback)
    '320118': ['adc'], '320130': ['adc', 'api'], '320144': ['api', 'adc', 'small'],
    '320140': ['cell', 'gene'], '320138': ['small', 'api'], '320136': ['small', 'api'],
    '320141': ['api'], '320126': ['protein', 'mab'], '320127': ['mab', 'protein', 'small', 'device'],
    '320147': ['small', 'protein'], '320125': ['small', 'mab', 'protein', 'cell', 'gene'],
    '320120': ['api', 'small', 'protein', 'mab'],
}

def kind(r):
    room, loc = r['Room'], r['Location']
    if room.startswith('Track 1') and 'Roundtables' in loc: return 'roundtable'
    if room.startswith('Track'): return 'talk'
    return 'social'

# Enrichment scraped from the public session pages (sponsor, description, speakers).
# Partial: only sessions present in session_scrape/sessions.jsonl have it.
SCRAPE = {}
sj = ROOT / 'scripts' / 'session_scrape' / 'sessions.jsonl'
if sj.exists():
    for line in sj.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            speakers = []
            for sp in d.get('spk', []):
                name, _, rest = sp.partition(' | ')
                role, _, org = rest.partition(' • ')
                speakers.append({'name': name.strip(), 'role': role.strip(), 'org': org.strip()})
            SCRAPE[d['id']] = {'sponsor': d.get('sp', ''), 'description': d.get('d', ''), 'speakers': speakers}

out = []
for i, r in enumerate(rows):
    day = 0 if i == 0 else (1 if i < DAY2_START else 2)
    out.append({
        'id': r['Session ID'], 'title': r['Session Title'].strip(),
        'day': day, 'date': DATES[day][0], 'day_label': DATES[day][1],
        'start': r['Start Time'].strip(), 'end': r['End Time'].strip(),
        'track': 'Track 1 · External Manufacturing Strategy' if r['Room'].startswith('Track 1')
                 else 'Track 2 · Technical Operations + CMC' if r['Room'].startswith('Track 2') else r['Room'],
        'kind': kind(r), 'link': r['Session Link'],
        'known_orgs': KNOWN_ORGS.get(r['Session ID'], []),
        'mods': MODS.get(r['Session ID'], []),
        'sponsor': SCRAPE.get(r['Session ID'], {}).get('sponsor', ''),
        'description': SCRAPE.get(r['Session ID'], {}).get('description', ''),
        'speakers': SCRAPE.get(r['Session ID'], {}).get('speakers', []),
        'detail': r['Session ID'] in SCRAPE,
    })
(ROOT / 'concierge' / 'recs' / 'sessions.json').write_text(json.dumps(out, indent=1))
print(len(out), 'sessions;', sum(1 for s in out if s['kind'] != 'social'), 'content sessions')
