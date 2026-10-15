"""Compare researched batches (scripts/enrichment_batches/out_*.json) with
scripts/company_enrichment.json. `--apply` writes the researched values in."""
import glob, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
cur = json.loads((HERE / 'company_enrichment.json').read_text())
new = {}
for f in sorted(glob.glob(str(HERE / 'enrichment_batches' / 'out_*.json'))):
    new.update(json.loads(Path(f).read_text()))

changed = same = 0
for k, v in new.items():
    old = cur.get(k, {})
    om, nm = set(old.get('modalities', [])), set(v['modalities'])
    od, nd = old.get('domain', ''), v['domain']
    if om == nm and od == nd:
        same += 1
        continue
    changed += 1
    print(f"{k} [{v['confidence']}]")
    if om != nm:
        print(f"   modalities: -{sorted(om - nm)} +{sorted(nm - om)}  => {sorted(nm)}")
    if od != nd:
        print(f"   domain: {od!r} -> {nd!r}")
print(f"\n{len(new)} researched; {changed} differ, {same} unchanged", file=sys.stderr)

if '--apply' in sys.argv:
    for k, v in new.items():
        # low confidence: keep the domain but don't pre-select a shaky guess for the visitor
        mods = [] if v['confidence'] == 'low' else v['modalities']
        cur.setdefault(k, {}).update(domain=v['domain'], modalities=mods, confidence=v['confidence'],
                                     evidence=v.get('evidence', ''), source=v.get('source', ''))
    (HERE / 'company_enrichment.json').write_text(json.dumps(cur, indent=1))
    print('applied', file=sys.stderr)
