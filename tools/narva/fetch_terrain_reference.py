"""Read a pinned public Bohemia sample tree and only small text reference files."""
from pathlib import Path
import hashlib, json, urllib.request, time

out=Path(__file__).resolve().parent/'official-terrain'
out.mkdir(exist_ok=True)
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'DayZ-terrain-reference/1.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=30) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
if (out/'tree.json').exists():
    saved=json.loads((out/'tree.json').read_text())
    ref, entries=saved['commit'],saved['entries']
else:
    ref=json.loads(fetch('https://api.github.com/repos/BohemiaInteractive/DayZ-Samples/commits/master'))['sha']
    tree=json.loads(fetch('https://api.github.com/repos/BohemiaInteractive/DayZ-Samples/git/trees/'+ref+'?recursive=1'))
    entries=[e for e in tree['tree'] if e['path'].startswith('Test_Terrain/')]
(out/'tree.json').write_text(json.dumps({'commit':ref,'entries':entries},indent=2)+'\n')
records=[]
for entry in entries:
    path=entry['path']
    if entry['type']!='blob' or entry.get('size',0)>150000:
        continue
    if not (path.startswith('Test_Terrain/world/') and path.endswith(('.cpp','.hpp','.cfg','.txt')) or
            path in ('Test_Terrain/data/config.cpp','Test_Terrain/readme.txt','Test_Terrain/README.md','Test_Terrain/ce/config.cpp') or
            path.startswith('Test_Terrain/ce/') and path.endswith('.xml')):
        continue
    url='https://raw.githubusercontent.com/BohemiaInteractive/DayZ-Samples/'+ref+'/'+path
    target=out/path
    data=target.read_bytes() if target.exists() else b''
    git_hash=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if git_hash != entry['sha']:
        data=fetch(url)
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==entry['sha'], path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    records.append({'path':path,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(out/'sources.json').write_text(json.dumps({'commit':ref,'files':records},indent=2)+'\n')
print(json.dumps({'commit':ref,'files':records},indent=2))
