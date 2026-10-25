"""Keep authentic original bytes beside review copies when removing trailing blank lines."""
from pathlib import Path
import json,hashlib,subprocess,re
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda b:hashlib.sha256(b).hexdigest()
r=subprocess.run(['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check','--','*.py','*.ps1','*.md','*.c','*.csv'],cwd=W,capture_output=True,text=True)
lines=[line for line in r.stdout.splitlines() if line]
assert all(line.endswith(': new blank line at EOF.') for line in lines),r.stdout
records=[]
for line in lines:
    rel=re.sub(r':\d+: new blank line at EOF\.$','',line)
    p=W/rel;assert rel.startswith('evidence/')
    raw=p.read_bytes();newline=b'\r\n' if b'\r\n' in raw else b'\n'
    normalized=raw.rstrip(b'\r\n')+newline;assert normalized!=raw
    base=W/Path(rel).parts[0]/Path(rel).parts[1]
    archive=base/'raw-preserved-sources'/Path(*Path(rel).parts[2:])
    archive=archive.with_name(archive.name+'.txt');archive.parent.mkdir(parents=True,exist_ok=True)
    assert not archive.exists();archive.write_bytes(raw);p.write_bytes(normalized)
    records.append(dict(review_copy=str(p.relative_to(base)).replace('\\','/'),original_copy=str(archive.relative_to(base)).replace('\\','/'),
        original_sha256=sha(raw),review_sha256=sha(normalized),evidence_root=str(base),normalization='Trailing blank lines only; original bytes retained verbatim.'))
for base in sorted({r['evidence_root'] for r in records}):
    rows=[r for r in records if r['evidence_root']==base];root=Path(base)
    (root/'source-copy-normalization.json').write_text(json.dumps(rows,indent=2)+'\n')
    bycopy={r['review_copy']:r for r in rows}
    for manifest in root.glob('preserved-files*.json'):
        data=json.loads(manifest.read_text());changed=False
        if not isinstance(data,list):continue
        for item in data:
            key=item.get('copy','').replace('\\','/')
            if key not in bycopy:continue
            row=bycopy[key];assert item['sha256']==row['original_sha256']
            item['copy']=row['original_copy'];item['review_copy']=row['review_copy'];item['review_sha256']=row['review_sha256'];changed=True
        if changed:manifest.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(normalized_review_copies=len(records),all_original_bytes_preserved=True)))
