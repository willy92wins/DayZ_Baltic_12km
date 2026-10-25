"""Re-anchor previously fixed probe sources; no renewed runtime acceptance."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
reference = W/'evidence/v30-bug-recheck-2026-10-08/historical-source-identities.json'
prior = json.loads(reference.read_text(encoding='utf-8'))
rows = []
for bug, entry in prior.items():
    for item in entry['files']:
        p = Path(item['file'])
        actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        rows.append({'bug': bug, 'file': str(p), 'expected': item['expected'],
                     'actual': actual, 'exact': actual == item['expected']})
result = {'status': 'SOURCE_IDENTITIES_PRESERVED' if all(x['exact'] for x in rows) else 'SOURCE_DRIFT',
          'checked_utc': datetime.now(timezone.utc).isoformat(),
          'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
          'files': rows, 'limits': ['Source identity only. These hashes do not revalidate navigation, final navmesh or runtime on a new terrain.']}
(ROOT/'historical-fixes-recheck.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'files': len(rows), 'mismatches': [x['file'] for x in rows if not x['exact']]}))
