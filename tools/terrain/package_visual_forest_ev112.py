"""Read every compiled forest object in compact arrays; package only WRP/config.

OPRW discovery uses the bounded model-table / anchor / map-info checks of the
technical pilot reader. It is a heuristic object reader, not a height decoder.
"""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'vegetation'),str(HERE.parent/'playtest')]
from prune_visual_forest_v31 import prefix,objects
from attach_navmesh import read_pbo
from package_visual_pilot_ev112 import norm,sha


def source_arrays(path,count):
    ids=np.empty(count,'<u4');mi=np.empty(count,'<u4');mat=np.empty((count,12),'<f4');names=[];index={};n=0
    with path.open('rb') as f:
        pre=prefix(f)
        for ident,name,raw in objects(f):
            assert n<count
            name=norm(name)
            if name not in index:index[name]=len(names);names.append(name)
            ids[n]=ident;mi[n]=index[name];mat[n]=struct.unpack_from('<12f',raw);n+=1
    assert n==count and np.isfinite(mat).all() and len(np.unique(ids))==n
    return dict(ids=ids,mi=mi,mat=mat,names=names,prefix_sha256=sha(pre))


def compiled_arrays(b,anchor):
    assert b[:4]==b'OPRW';version=struct.unpack_from('<I',b,4)[0];stride={29:60,32:64}[version]
    mark=b.find(b'baltic_water_v30\\');assert mark>=4;possible=[]
    for start in range(max(0,mark-4000),mark-3):
        count=struct.unpack_from('<I',b,start)[0]
        if not 0<count<200000:continue
        p=start+4;names=[]
        try:
            for _ in range(count):
                end=b.index(b'\0',p,p+300);name=b[p:end].decode('ascii')
                if not name.lower().endswith('.p3d'):raise ValueError()
                names.append(norm(name));p=end+1
            if start+4<=mark<p:possible.append((names,p))
        except (ValueError,UnicodeDecodeError):pass
    assert len(possible)==1,('ambiguous model table',len(possible))
    names,mend=possible[0];needle=struct.pack('<2I',anchor['id'],names.index(norm(anchor['name'])));hits=[];p=mend
    while True:
        p=b.find(needle,p)
        if p<0:break
        if p+stride<=len(b) and np.max(np.abs(np.array(struct.unpack_from('<12f',b,p+8))-anchor['matrix']))<=1e-5:hits.append(p)
        p+=1
    assert len(hits)==1,('ambiguous anchor',hits)
    dtype=np.dtype(dict(names=['ids','mi','mat','shape']+(['reserved'] if stride==64 else []),
                        formats=['<u4','<u4',('<f4',12),'<u4']+(['<u4'] if stride==64 else []),
                        offsets=[0,4,8,56]+([60] if stride==64 else []),itemsize=stride))
    def valid(rows):
        mat=rows['mat'];length=np.linalg.norm(mat[:,:9].reshape(-1,3,3),axis=2)
        ok=(rows['ids']>0)&(rows['mi']<len(names))&(rows['shape']<=64)&np.isfinite(mat).all(1)&(np.abs(mat[:,9:]).max(1)<1e6)
        ok&=((length>1e-5).all(1)|(length==0).all(1))&(length<100).all(1)
        if stride==64:ok&=rows['reserved']==0
        return ok
    first=hits[0]
    while first-stride>=mend:
        count=min(65536,(first-mend)//stride);start=first-count*stride
        bad=np.flatnonzero(~valid(np.frombuffer(b,dtype,count=count,offset=start)))
        if len(bad):first=start+(int(bad[-1])+1)*stride;break
        first=start
    p=first
    while p+stride<=len(b):
        count=min(65536,(len(b)-p)//stride);rows=np.frombuffer(b,dtype,count=count,offset=p);ok=valid(rows)
        bad=np.flatnonzero(~ok)
        if len(bad):p+=int(bad[0])*stride;break
        p+=count*stride
    data=np.frombuffer(b,dtype,count=(p-first)//stride,offset=first)
    assert len(np.unique(data['ids']))==len(data)
    after=struct.unpack_from('<2I',b,p);assert after[0]<=64 and np.any(data['ids']==after[1]),('map info',after)
    return dict(ids=data['ids'],mi=data['mi'],mat=data['mat'],names=names),dict(version=version,stride=stride,table=[first,p],after=list(after),model_count=len(names))


def compare(s,c):
    assert len(s['ids'])==len(c['ids']),'object count'
    si=np.argsort(s['ids']);ci=np.argsort(c['ids'])
    assert len(np.unique(c['ids']))==len(ci) and np.array_equal(s['ids'][si],c['ids'][ci]),'object IDs'
    sn=np.array(s['names']);cn=np.array(c['names']);maximum=0.;pilot=0;rounded=[]
    for start in range(0,len(si),65536):
        a=si[start:start+65536];b=ci[start:start+65536];names=sn[s['mi'][a]]
        assert np.array_equal(names,cn[c['mi'][b]]),'object models'
        components=np.abs(s['mat'][a]-c['mat'][b]);delta=components.max(1);maximum=max(maximum,float(delta.max()))
        ok=components<=1e-5
        # One observed compiled fallen tree differs by 2 float32 ULP in Y.
        # This format allowance is forest-Y-only and must additionally pass
        # the independent 5mm root consumer below. No allowance for pilot poses.
        forest=np.isin(names,list(s.get('forest_models',())))
        ulp=2*np.abs(np.spacing(s['mat'][a,10]))
        exception=forest&~ok[:,10]&(components[:,10]<=ulp)
        for j in np.flatnonzero(exception):rounded.append(dict(id=int(s['ids'][a[j]]),model=str(names[j]),source=s['mat'][a[j]].tolist(),compiled=c['mat'][b[j]].tolist(),delta_y=float(components[j,10]),two_ulp=float(ulp[j])))
        ok[:,10]|=exception
        assert np.isfinite(delta).all() and ok.all(),'object matrix'
        is_pilot=np.char.startswith(names,'baltic_stream_pilot\\');assert (delta[is_pilot]==0).all(),'pilot matrix'
        pilot+=int(is_pilot.sum())
    return dict(objects=len(si),pilot_exact=pilot,max_matrix_delta=maximum,forest_y_rounding=rounded)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage');ap.add_argument('output');a=ap.parse_args();S=Path(a.stage);out=Path(a.output);assert not out.exists()
    source=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    review=json.loads((S/'forest-support-review-full.json').read_text());assert review['status']=='SUPPORT_CLEARANCE_PASS' and sha(source.read_bytes())==review['source_wrp_sha256']
    sr=json.loads((S/'stage-report.json').read_text());count=sr['remaining_objects']+35
    s=source_arrays(source,count);reference=json.loads(Path(sr['forest_reference']['path']).read_text())['models'];s['forest_models']=set(reference)
    print('Source objects',len(s['ids']),flush=True)
    compiled,_,new=read_pbo(S/'out/narva_trial.pbo')
    anchor=dict(id=int(s['ids'][0]),name=s['names'][s['mi'][0]],matrix=s['mat'][0])
    c,reader=compiled_arrays(new['baltic_trial.wrp'],anchor);parity=compare(s,c);assert parity['pilot_exact']==35
    sys.path.insert(0,str(S.parent/'forest-final-tools/r2/gates'));import geom
    terrain=Path(sr['merged'])/'terrain-buried.npz'
    H=np.load(terrain)['heights']
    assert sha(terrain.read_bytes())==review['terrain_sha256']
    for row in parity['forest_y_rounding']:
        m=np.array(row['compiled']);root=m[9:]-m[:9].reshape(3,3).T@np.array(reference[row['model']]['bc'])
        row['compiled_root_error_m']=float(root[1]-geom.h_at(H,np.array([root[0]]),np.array([root[2]]))[0])
        assert abs(row['compiled_root_error_m'])<=.005,'compiled forest root'
        assert row['source'][:10]==row['compiled'][:10] and row['source'][11]==row['compiled'][11],'rounding changes XY/rotation'
    print('Compiled objects',json.dumps(parity),flush=True)
    # Three known-bad versions of real records, through this exact comparator.
    take=np.arange(min(1000,len(s['ids'])));small={k:(v[take].copy() if k in ('ids','mi','mat') else v) for k,v in s.items()}
    negatives={}
    for test in ('missing','extra','moved'):
        bad={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in small.items()}
        if test=='missing':
            for key in ('ids','mi','mat'):bad[key]=bad[key][1:]
        elif test=='extra':
            for key in ('ids','mi','mat'):bad[key]=np.concatenate([bad[key],bad[key][:1]])
            bad['ids'][-1]=int(s['ids'].max())+1
        else:bad['mat'][0,10]+=.1
        try:compare(small,bad)
        except AssertionError:negatives[test]=True
        else:negatives[test]=False
    assert all(negatives.values());del s,c
    baseline=Path('P:/Mods/@DayZ_Baltic_EV112_RuntimeMarginsV2/Addons/narva_trial.pbo')
    raw,props,before=read_pbo(baseline);assert sha(raw)=='751823ac65cd56c9093de9705ee30b08a448a69606690c1363ecf944a15ac838'
    out.mkdir(parents=True);(out/'config.bin').write_bytes(new['config.bin'])
    converter='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe'
    p=subprocess.run([converter,'-txt','-dst',str(out/'config.cpp'),str(out/'config.bin')],capture_output=True);(out/'decode.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
    updated=(out/'config.cpp').read_text(encoding='utf-8-sig');original=(S/'baseline-config.cpp').read_text(encoding='utf-8-sig')
    assert updated.count('"Baltic_Stream_Pilot"')==1
    assert re.sub(r'\s+','',re.sub(r',\s*"Baltic_Stream_Pilot"','',updated))==re.sub(r'\s+','',original),'unexpected config change'
    expected=dict(before)
    for entry in ('baltic_trial.wrp','config.bin'):expected[entry]=new[entry]
    folder=out/'compiled/narva_trial';folder.mkdir(parents=True);dest=out/'Addons';dest.mkdir()
    for name,data in expected.items():
        path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    bank='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe';argv=[bank]
    for key,value in props.items():argv+=['-property',key+'='+value]
    p=subprocess.run(argv+['-dst',str(dest),str(folder)],capture_output=True);(out/'filebank.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
    packed,finalprops,final=read_pbo(dest/'narva_trial.pbo');assert final==expected and all(finalprops.get(k)==v for k,v in props.items())
    report=dict(status='OFFLINE_PACKAGE_PASS',forest=True,forest_instances=review['instances'],objects=parity,reader=reader,negative_controls=negatives,
                baseline_sha256=sha(raw),compiled_pbo_sha256=sha(compiled),pbo_sha256=sha(packed),wrp_sha256=sha(final['baltic_trial.wrp']),source_wrp_sha256=sha(source.read_bytes()),
                entries_unchanged=len(before)-2,changed_entries=['baltic_trial.wrp','config.bin'],config_delta='requiredAddons += Baltic_Stream_Pilot',
                limits=['Object-table discovery remains heuristic; no compiled-height decoder.',
                        'Offline artifact verification only; water, collision, visual, AI and performance acceptance separate.'])
    (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
