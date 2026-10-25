from pathlib import Path
import datetime, hashlib, json, shutil

O = Path(__file__).parent
W = Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
A = W / 'evidence/v31-pond-layer-2026-10-13/ev112/integration/runtime-b-20261019'
S = A / 'supplement'
assert not S.exists(), 'Do not overwrite an existing supplement'
raw = (O / 'vault-link-audit-runtime-b.log').read_text(encoding='utf-8-sig')
valid = (O / 'vault-link-audit-runtime-b-valid-baseline.log').read_text(encoding='utf-8-sig')
assert 'baseline_pairs=0' in raw
assert 'link_audit_status=' in valid
fields = dict(line.split('=', 1) for line in valid.splitlines() if '=' in line and not line.startswith(' '))
assert int(fields['baseline_pairs']) > 0
assert fields['missing_session_index'] == '0'
S.mkdir()
entries = []
for name in ['finalize-runtime-b-supplement.py', 'verify-runtime-b-closeout.py', 'repair-runtime-b-newlines.py', 'runtime-b-newline-repair.json', 'vault-link-audit-runtime-b.log', 'vault-link-audit-runtime-b-valid-baseline.log']:
    src = O / name
    dst = S / name
    shutil.copyfile(src, dst)
    data = dst.read_bytes()
    assert data == src.read_bytes()
    entries.append(dict(file=name, source=str(src), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
result = dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    files=entries, global_audit=fields,
    invalid_baseline_note='The prescribed runbook command uses baseline-control.json, whose schema is skill-drift-control/v1. The link auditor expects source -> target lines and parsed zero pairs. That attempt is retained; its new_live_pairs cannot establish regressions. The second audit uses the frozen link-pair inventory.',
    acceptance='Owned closeout checks are in ../closeout-verification.json. A global FAIL is preserved and does not become PASS. Unrelated vault debt was not edited.')
(S / 'MANIFEST.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (A / 'README.md').open('a', encoding='utf-8', newline='\n') as f:
    f.write('\nControl del cierre: [verificación local](closeout-verification.json), 299 archivos contrastados por SHA256. [Auditoría documental y reparación de saltos de línea](supplement/MANIFEST.json): la primera auditoría usó la referencia incorrecta indicada por el runbook; la repetición con el inventario de enlaces válido conserva el resultado global **' + fields['link_audit_status'] + '** (' + fields['new_live_pairs'] + ' parejas nuevas respecto a esa referencia; ninguna sesión sin índice). No equivale a una regresión causada por EV112 ni a un PASS global.\n')
print(json.dumps(dict(status='SUPPLEMENT_SAVED', files=len(entries), global_audit=fields['link_audit_status'], baseline_pairs=fields['baseline_pairs']), indent=2))
