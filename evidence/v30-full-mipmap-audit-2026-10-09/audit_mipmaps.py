from pathlib import Path
import hashlib,io,json,struct,sys,time,subprocess,copy
import numpy as np
from PIL import Image
B=Path(__file__).parent
PACK=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-3d-viewer')
LZO=Path('C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(PACK),str(LZO),str(W/'tools/playtest')]
from dayz_3d_viewer.paa_to_png import PAAFile,decode_dxt_mipmap,expected_raw_size
from lzo_decompress import decompress_lzo
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
CURRENT=Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons/narva_trial.pbo')
PREVIOUS=Path('P:/Mods/@DayZ_Baltic_HingeSmoothV1/Addons/narva_trial.pbo')
SURFACE=Path('E:/DayZ-Baltic-Build/v30-current-satellite-20261009')
TOOL=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/ImageToPAA/ImageToPAA.exe')

def strict_parse(blob):
    p=2;tags={};tagpositions={}
    assert len(blob)>=10
    while blob[p:p+4]==b'GGAT':
        assert p+12<=len(blob)
        tag=blob[p+4:p+8][::-1].decode('ascii');size=struct.unpack_from('<I',blob,p+8)[0]
        assert p+12+size<=len(blob);tags[tag]=blob[p+12:p+12+size];tagpositions[tag]=p+12;p+=12+size
    assert blob[p:p+2]==b'\0\0';p+=2;offsets=[];headers=[]
    while True:
        assert p+4<=len(blob),'missing mip header/terminator'
        w,h=struct.unpack_from('<HH',blob,p)
        if w==h==0:
            p+=4;assert not any(blob[p:]),'unexpected trailing data';break
        assert p+7<=len(blob);size=int.from_bytes(blob[p+4:p+7],'little')
        assert size>0 and p+7+size<=len(blob),'truncated payload'
        offsets.append(p);headers.append((w&0x7fff,h));p+=7+size
    assert headers==[(n,n) for n in [512,256,128,64,32,16,8,4]],('incomplete chain',headers)
    assert 'OFFS' in tags and len(tags['OFFS'])%4==0
    table=list(struct.unpack('<'+'I'*(len(tags['OFFS'])//4),tags['OFFS']))
    assert table[:len(offsets)]==offsets and not any(table[len(offsets):]),'wrong OFFS'
    q=PAAFile(fileobj=io.BytesIO(blob));assert len(q.mipmaps)==len(offsets)
    assert all(len(m['data'])==m['data_size'] for m in q.mipmaps)
    return q,offsets,tagpositions

def pixels(q,index):
    m=q.mipmaps[index];size=expected_raw_size(q.paa_type,m['width'],m['height']);raw=m['data']
    if m['lzo']:
        raw,consumed=decompress_lzo(raw,0,size,std_m4=True)
        assert consumed==m['data_size'],'unconsumed LZO bytes'
    assert len(raw)==size,'no silent padding or excess bytes'
    im=decode_dxt_mipmap(raw,m['width'],m['height'],q.paa_type).convert('RGBA')
    return np.array(im),raw

def verify_one(blob,kind,native=None):
    q,_,_=strict_parse(blob);assert q.paa_type==(0xff01 if kind=='s' else 0xff05)
    levels=[];largest=None
    for index,m in enumerate(q.mipmaps):
        a,_=pixels(q,index)
        assert a.shape==(m['height'],m['width'],4)
        if index==0:largest=a
        levels.append(dict(size=m['width'],stored_bytes=m['data_size'],compressed=m['lzo'],pixel_sha256=digest(a.tobytes()),
            rgb_mean=a[:,:,:3].mean(axis=(0,1)).tolist(),black_pixels=int(np.all(a[:,:,:3]==0,axis=2).sum()),nonopaque_pixels=int((a[:,:,3]!=255).sum())))
    assert all(l['nonopaque_pixels']==0 for l in levels),'unexpected alpha'
    if kind=='s':assert all(any(c>0 for c in l['rgb_mean']) for l in levels),'empty satellite mip'
    delta=None
    if native is not None:
        n=np.array(Image.open(native).convert('RGBA'));assert largest.shape==n.shape
        delta=int(abs(largest.astype(int)-n).max())
        assert delta<=2,('independent decoder mismatch',native,delta)
    return dict(type=q.type_name,levels=levels,native_largest_max_difference=delta)

def must_reject(label,blob):
    try:strict_parse(blob)
    except (AssertionError,IndexError,ValueError,struct.error):return label
    raise AssertionError('negative accepted: '+label)

def isolate_native(blob,name,index):
    q,_,_=strict_parse(blob);m=q.mipmaps[index];a,raw=pixels(q,index)
    # Only the selected mip's original DXT blocks; ImageToPAA must consume them independently.
    encoded=struct.pack('<HHHH',q.paa_type,0,m['width'],m['height'])+len(raw).to_bytes(3,'little')+raw+b'\0'*6
    folder=B/'native-controls';folder.mkdir(exist_ok=True)
    stem=Path(name).stem;path=folder/(stem+f'_mip{m["width"]}'+('_lco.paa' if stem.startswith('s_') else '_lca.paa'))
    target=path.with_suffix('.png');path.write_bytes(encoded)
    r=subprocess.run([str(TOOL),str(path),str(target)],capture_output=True,text=True)
    assert r.returncode==0 and target.is_file(),(name,index,r.stdout,r.stderr)
    n=np.array(Image.open(target).convert('RGBA'));assert a.shape==n.shape
    delta=int(abs(a.astype(int)-n).max());assert delta<=2,(name,index,delta)
    return dict(name=name,size=m['width'],paa_sha256=sha(path),native_png_sha256=sha(target),max_decoder_difference=delta)

if __name__=='__main__':
    start=time.monotonic()
    assert sha(CURRENT)=='b69265c5feb99d1bda7a5c9f02282818d0ffe4cd26f89f3a095c128e62d374f3'
    assert sha(PREVIOUS)=='9eb9f4006c55e3ed3f73461816bed0272e8ab5fdc2f0ca58e214687ef0b82ee5'
    refs=[]
    for name in ['s_000_000_lco.paa','m_000_000_lca.paa']:
        p=Path('P:/DZ/worlds/chernarusplus/data/layers')/name
        q,_,_=strict_parse(p.read_bytes());refs.append(dict(path=str(p),sha256=sha(p),info=q.info()))
    raw,_,entries=read_pbo(CURRENT);del raw
    textures={name:blob for name,blob in entries.items() if Path(name).name.startswith(('s_','m_')) and name.endswith(('_lco.paa','_lca.paa'))};assert len(textures)==2048
    del entries
    first=next(blob for name,blob in textures.items() if Path(name).name=='s_027_021_lco.paa')
    _,offsets,tags=strict_parse(first);mutant=bytearray(first);struct.pack_into('<I',mutant,tags['OFFS'],offsets[0]+1)
    negatives=[must_reject('truncated_payload_rejected',first[:-12]),must_reject('wrong_mip_offset_rejected',bytes(mutant)),
               must_reject('missing_last_mip_rejected',first[:offsets[-1]]+b'\0'*6)]
    cache={};current=[];native_controls=[]
    for i,(name,blob) in enumerate(sorted(textures.items())):
        base=Path(name).name;h=digest(blob)
        assert (SURFACE/'surface/layers'/base).read_bytes()==blob
        result=verify_one(blob,base[0],SURFACE/'decoded'/Path(base).with_suffix('.png'))
        cache[h]=result;current.append(dict(name=name,sha256=h,**result))
        if base in {'s_027_021_lco.paa','m_027_021_lca.paa','s_004_015_lco.paa','m_004_015_lca.paa'}:
            for index in [3,5,7]:native_controls.append(isolate_native(blob,name,index))
        if i%256==255:print(f'Current {i+1}/2048: all eight mips and native largest decoded',flush=True)
    del textures
    raw,_,entries=read_pbo(PREVIOUS);del raw
    old=[];reused=0
    for name,blob in sorted(entries.items()):
        base=Path(name).name
        if not(base.startswith(('s_','m_')) and base.endswith(('_lco.paa','_lca.paa'))):continue
        h=digest(blob)
        if h in cache:result=cache[h];reused+=1
        else:result=verify_one(blob,base[0]);cache[h]=result
        old.append(dict(name=name,sha256=h,**result))
        if len(old)%512==0:print(f'Previous {len(old)}/2048 inventoried',flush=True)
    assert len(old)==2048
    report=dict(status='PASS_CURRENT_AND_PRIOR_MIP_FILE_INTEGRITY',current_textures=2048,current_mips=16384,previous_textures=2048,
        previous_mips=16384,previous_reused_exact_payloads=reused,negative_controls=negatives,native_isolated_controls=native_controls,
        native_largest_max_difference=max(r['native_largest_max_difference'] for r in current),reference=refs,
        current=current,previous=old,inputs={str(p):sha(p) for p in [CURRENT,PREVIOUS,TOOL,PACK/'dayz_3d_viewer/paa_to_png.py',LZO/'lzo_decompress.py']},
        seconds=time.monotonic()-start,limits=['File integrity/decoder tests, not proof of native mip streaming or GPU residency.',
            'The current and prior packages both pass this scope; no missing-mip root cause or gray-tile fix is inferred.',
            'Color/detail averaging and surface mixing at distance are expected; no global aesthetic acceptance inferred.'])
    (B/'mipmap-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['current','previous']},indent=2))
