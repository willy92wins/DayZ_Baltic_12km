from pathlib import Path
import hashlib,json,shutil
E=Path(__file__).parent
S=E.parent/'v30-complete-dry-surface-20261009'
original=(S/'verify_native.py').read_text()
before="log=Path('P:/DayZ_MCP_dev/_server/profiles/baltic_base_surface_fullwater_v1.log')"
after="log=E/'native-snapshot.log'"
assert original.count(before)==1
changed=original.replace(before,after)
assert changed.replace(after,before)==original
log=Path('P:/DayZ_MCP_dev/_server/profiles/baltic_base_surface_fullwater_v1.log')
snapshot=log.read_bytes()
assert b'END;4194304;0;1212;' in snapshot
(E/'native-snapshot.log').write_bytes(snapshot)
(E/'verify_native.py').write_text(changed)
shutil.copyfile(S/'base-surface-fullwater-reference.json',E/'base-surface-fullwater-reference.json')
sha=lambda b:hashlib.sha256(b).hexdigest()
(E/'snapshot-provenance.json').write_text(json.dumps(dict(run_id='ef3f2fe4-98bb-4878-9a06-1f532934f111',source_log=str(log),snapshot_sha256=sha(snapshot),original_consumer_sha256=sha((S/'verify_native.py').read_bytes()),adaptation='Input path only; all gates unchanged',old_line=before,new_line=after),indent=2)+'\n')
print('Snapshot preserved; consumer input path only changed.')
