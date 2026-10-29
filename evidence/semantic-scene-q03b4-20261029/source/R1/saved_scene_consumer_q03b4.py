"""Source-rereading consumer. Never imports producer or its semantic functions."""
import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from pathlib import Path
from collections import Counter
import numpy as np
import saved_scene_io_q03b4 as IO
G=('bed','water','unknown','road_bed','road_water','road_unknown')
X=('source_grid','source_triangles','body_row_min','body_row_max','body_col_min','body_col_max','source_category','bed_source_face','npz_start','cap_before','cap_after')
M=[['model','<i4'],['source_model','<i4'],['face','<i4'],['section','<i4'],['lod','<i4'],['kind','|u1'],['vertices','|u1'],['flags','|u1'],['proxy','<i4'],['planarity_m','<f8']]
def ensure(ok,code='REPORT'):IO.require(ok,code)
def canonical(value):
    ensure(type(value) is str and value.isascii() and ':' not in value and all(ord(x)>=32 for x in value),'SCHEMA')
    parts=value.replace('\\','/').strip('/').lower().split('/');ensure(all(x not in ('','.','..') for x in parts),'SCHEMA');return '/'.join(parts)
def member_list(k):
    if k=='prototypes':return ('vertices','meta')
    if k=='instances':return ('ids','model_index','matrix','norm','determinant','nonorthogonality')
    if k=='selected':return ('ids','model_index','matrix')
    return tuple(v+s for v in G for s in ('','_n','_flags','_source_ids'))+X
def validate_headers(h,kind,counts,p=None):
    rules={}
    def rule(n,t,sh):rules[n+'.npy']=(t,sh)
    if kind=='prototypes':rule('vertices',('<f8',),[counts['prototype_faces'],4,3]);rule('meta',(M,),[counts['prototype_faces']])
    elif kind in ('instances','selected'):
        for n in ('ids','model_index'):rule(n,('<u8','<u4','<i8','<i4'),[counts['instances']])
        rule('matrix',('<f8','<f4'),[counts['instances'],12])
        if kind=='instances':
            for n in ('norm','determinant','nonorthogonality'):rule(n,('<f8',),[counts['instances'],3] if n=='norm' else [counts['instances']])
    else:
        for name in G:
            f=p['faces'][name];ensure(type(f) is int and f>=0,'SCHEMA')
            rule(name,('<f8',),[f,4,3]);rule(name+'_n',('|u1',),[f]);rule(name+'_flags',('|u1',),[f]);rule(name+'_source_ids',('<i4',),[f,2])
        b=p['faces']['bed'];grid=h['source_grid.npy']['shape'];ensure(len(grid)==3 and grid[2]==3 and min(grid[:2])>=2 and grid[0]*grid[1]<=3*b,'GRID')
        rule('source_grid',('<f8',),grid);rule('source_triangles',('<i8','<i4'),[b,3]);rule('source_category',('<U9',),[b]);rule('bed_source_face',('<i4',),[b])
        for n in X[2:6]:rule(n,('<i8','<i4'),[b])
        for n in X[8:]:rule(n,('<i4',),[])
    ensure(set(rules)==set(h),'SCHEMA')
    for name,(types,shape) in rules.items():ensure(any(IO.exact(h[name]['dtype'],t) for t in types) and IO.exact(h[name]['shape'],shape),'SCHEMA')
def catalogs(raw,section_rows):
    source={};models={};names={}
    for a in raw:
        IO.keys(a,['index','name','instances','group']);ensure(type(a['index']) is int and type(a['instances']) is int and a['index']>=0 and a['instances']>=0,'SCHEMA');ensure(a['index'] not in source,'IDENTITY');source[a['index']]=a
    ensure(len({canonical(x['name']) for x in raw})==len(raw),'IDENTITY')
    for a in section_rows:
        IO.keys(a,['index','name','lods','proxies','center']);i=a['index'];name=canonical(a['name']);ensure(type(i) is int and i>=0 and i not in models and name not in names,'IDENTITY');models[i]=a;names[name]=i
        ensure(len(a['center'])==3 and all(type(x) in (int,float) and np.isfinite(x) for x in a['center']),'SCHEMA')
        seen=set()
        for lod in a['lods']:
            IO.keys(lod,['index','resolution','faces','sections']);ensure(type(lod['index']) is int and lod['index']>=0 and lod['index'] not in seen,'IDENTITY');seen.add(lod['index'])
            ensure(type(lod['faces']) is int and lod['faces']>=0 and type(lod['resolution']) in (int,float) and np.isfinite(lod['resolution']),'SCHEMA')
            sections=set()
            for q in lod['sections']:
                IO.keys(q,['index','faces','material','material_raw','texture','texture_raw']);ensure(type(q['index']) is int and q['index']>=0 and q['index'] not in sections,'IDENTITY');sections.add(q['index']);ensure(type(q['faces']) is int and q['faces']>=0,'SCHEMA');ensure(all(type(q[x]) is str for x in ('material','material_raw','texture','texture_raw')),'SCHEMA')
            ensure(sum(q['faces'] for q in lod['sections'])==lod['faces'],'FACE')
        for q in a['proxies']:IO.keys(q,['model','matrix']);canonical(q['model']);ensure(len(q['matrix'])==12 and all(type(x) in (int,float) and np.isfinite(x) for x in q['matrix']),'SCHEMA')
    return source,models,names
def check_face(model,lod_id,sec,face,kind=None):
    choices=[x for x in model['lods'] if x['index']==lod_id];ensure(len(choices)==1,'FACE');l=choices[0]
    sections=[x for x in l['sections'] if x['index']==sec];ensure(len(sections)==1 and 0<=face<l['faces'],'FACE')
    if kind==0:ensure(l['resolution']==3000000028082176.0,'FACE')
    if kind in (1,2):
        candidates=sorted(x['resolution'] for x in model['lods'] if 0<=x['resolution']<1000)
        ensure(candidates and candidates.count(candidates[0])==1 and l['resolution']==candidates[0],'FACE')
        ensure(sections[0]['material'] in {'dz/water/ponds/data/pond_moss_1.rvmat','dz/water/streams/data/water_streambed.rvmat'},'FACE')
def verify_epoch(s,j):
    root=Path(s['source_root']);src=j['deployed-surface-prototypes-20261028/inputs.json'];pin=src['source_pins'];p=j['pilot-visible-surface-extraction-20261028/inputs.json']['pins']
    bindings=[(str(root/'package-kit7-fc-world-20261026/compiled/narva_trial/baltic_trial.wrp'),'wrp_compiled'),(str(root/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'),'wrp_editable'),('P:\\Mods\\@DayZ_Baltic_EV112_Kit7Nav8Load1\\Addons\\baltic_stream_pilot.pbo','pilot_pbo')]
    for k,v in bindings:ensure(k in pin and IO.exact(pin[k],s['epoch'][v]),'EPOCH')
    sp=s['pins']['deployed-surface-prototypes-20261028/inputs.json'];ensure(p.get(sp['path'])==sp['sha256'],'EPOCH')
    for a in s['arrays']:
        if a['kind']=='instances':ensure(p.get(a['path'])==a['sha256'],'EPOCH')
        if a['kind']=='selected':ensure(pin.get(a['path'])==a['sha256'],'EPOCH')
        manifest=src['discovery_artifacts'] if a['kind']=='selected' else j['pilot_manifest' if a['kind']=='pilot' else 'surface_manifest']
        ensure(a['relative'] in manifest,'EPOCH');b=manifest[a['relative']];ensure(b['sha256']==a['sha256'] and b['bytes']==a['bytes'],'EPOCH')
def consume(c,s,sha,report):
    IO.keys(report,c['report_keys']);ensure(report['schema']=='q03b4-report-v1' and report['contract_sha256']==sha and report['status']==c['status']);ensure(IO.exact(report['claims'],s['claims']) and IO.exact(report['limitations'],c['historical_claims']))
    reader=IO.Reader(c);j={k:reader.json(k,v) for k,v in s['pins'].items()};verify_epoch(s,j);expected=s['expected']
    cat,models,names=catalogs(j['deployed-surface-prototypes-20261028/model-catalog.json'],j['deployed-surface-prototypes-20261028/model-sections.json'])
    roots={i for i,v in cat.items() if v['group']!='vegetation_not_inspected'};extras=set(models)-set(cat)
    ensure(len(cat)==expected['source_models'] and len(models)==expected['prototype_models'] and len(extras)==expected['proxy_only_models'] and len(cat)-len(roots)==expected['vegetation_models_not_saved'],'COVERAGE')
    ensure(roots<=set(models) and all(canonical(cat[i]['name'])==canonical(models[i]['name']) for i in roots),'IDENTITY')
    routes=j['deployed-surface-prototypes-20261028/proxy-paths.json'];ensure(len(routes)==expected['proxy_paths'],'COVERAGE');ensure(IO.exact(routes,report['proxy_routes']))
    for route in routes:
        IO.keys(route,['root_model','slots','source_model']);ensure(type(route['root_model']) is int and type(route['source_model']) is int,'SCHEMA');ensure(type(route['slots']) is list and 0<len(route['slots'])<=16,'PROXY');current=route['root_model'];visited=[]
        for slot in route['slots']:
            ensure(type(slot) is list and len(slot)==2 and all(type(k) is int for k in slot),'SCHEMA');ensure(current in models and current not in visited and slot[0]==current,'PROXY');visited.append(current);ps=models[current]['proxies'];ensure(0<=slot[1]<len(ps),'PROXY');child=canonical(ps[slot[1]]['model']);ensure(child in names,'PROXY');current=names[child]
        ensure(current==route['source_model'] and current not in visited,'PROXY')
    model_records=report['models'];ensure(type(model_records) is list and len(model_records)==len(cat)+len(extras));ensure([x['index'] for x in model_records]==sorted(set(cat)|extras));rm={x['index']:x for x in model_records}
    archives=s['arrays'];base={x['kind']:x for x in archives if x['kind']!='pilot'};ensure(len(base)==3,'COVERAGE')
    counts=Counter();all_ranges=[]
    with reader.open(base['prototypes'],member_list('prototypes'),lambda h:validate_headers(h,'prototypes',expected)) as (a,d):
        meta=a['meta'];ensure(set(map(int,meta['model']))==roots and set(map(int,meta['source_model']))==set(models),'COVERAGE')
        ensure(np.isfinite(a['vertices']).all() and np.isfinite(meta['planarity_m']).all() and (meta['planarity_m']>=0).all(),'FACE')
        ensure(np.isin(meta['vertices'],[3,4]).all(),'FACE');ensure(not a['vertices'][meta['vertices']==3,3,:].view(np.uint64).any(),'PADDING')
        for mi in sorted(set(cat)|extras):
            row=rm[mi];IO.keys(row,['index','name','group','catalog_instance_count','pose_rows','runs','layers'])
            for run in row['runs']:
                IO.keys(run,['key','start','end']);ensure(type(run['start']) is int and type(run['end']) is int and 0<=run['start']<run['end']<=len(meta));ensure(type(run['key']) is list and len(run['key'])==5 and all(type(v) is int for v in run['key']));ensure(run['key'][0]==mi)
                lo,hi=run['start'],run['end'];all_ranges.append((lo,hi,run['key']))
                for pos in range(lo,hi):
                    m=meta[pos];actual=[int(m[f]) for f in ('model','source_model','lod','kind','proxy')];ensure(actual==run['key']);root,src,lod,kind,proxy=actual;ensure(kind in (0,1,2) and src in models,'FACE');check_face(models[src],lod,int(m['section']),int(m['face']),kind);flag=int(m['flags']);ensure(not flag&~7,'FACE')
                    if kind==2:ensure(0<=proxy<len(routes) and routes[proxy]['root_model']==root and routes[proxy]['source_model']==src and flag&1,'PROXY')
                    else:ensure(proxy==-1 and src==root and not flag&1,'PROXY')
                    counts[kind]+=1;counts['ambiguous']+=bool(flag&2);counts['degenerate']+=bool(flag&4)
        ordered=sorted(all_ranges);cursor=0;last=None
        for lo,hi,key in ordered:ensure(lo==cursor and key!=last);cursor=hi;last=key
        ensure(cursor==len(meta))
    del a
    for k,v in [(0,'roadway'),(1,'water_visual'),(2,'conditional_proxy'),('ambiguous','ambiguous'),('degenerate','degenerate')]:ensure(counts[k]==expected[v],'COVERAGE')
    with reader.open(base['instances'],member_list('instances'),lambda h:validate_headers(h,'instances',expected)) as (a,inst_digest):
        ids=a['ids'].copy();indices=a['model_index'].copy();ensure(len(set(map(int,ids)))==len(ids),'POSE')
        for k in ('matrix','norm','determinant','nonorthogonality'):ensure(np.isfinite(a[k]).all(),'POSE')
        ensure(Counter(map(int,indices))==Counter({i:cat[i]['instances'] for i in roots}),'POSE')
    del a
    with reader.open(base['selected'],member_list('selected'),lambda h:validate_headers(h,'selected',expected)) as (a,d):
        for n in ('ids.npy','model_index.npy','matrix.npy'):ensure(IO.exact(d[n],inst_digest[n]),'POSE')
    del a
    pilot_metadata={p['model_index']:p for p in j['pilot-visible-surface-extraction-20261028/models.json']};specs={p['model_index']:p for p in s['pilot_specs']};ensure(len(specs)==len(pilot_metadata)==expected['pilot_models'],'COVERAGE')
    ensure([p['model_index'] for p in report['pilots']]==sorted(specs));bound={p['model_index']:p for p in report['pilots']}
    for mi in sorted(specs):
        p=specs[mi];ensure(canonical(p['model'])==canonical(cat[mi]['name']),'POSE');loc=np.flatnonzero(indices==mi);ensure(len(loc)==1 and int(ids[loc[0]])==p['instance_id'],'POSE');ensure(all(IO.exact(pilot_metadata[mi][k],v) for k,v in p.items()),'IDENTITY')
        rel='pilot-visible-surface-extraction-20261028/'+p['file'];found=[q for q in archives if q['kind']=='pilot' and q['relative']==rel];ensure(len(found)==1 and pilot_metadata[mi]['sha256']==found[0]['sha256'],'COVERAGE');q=found[0]
        with reader.open(q,member_list('pilot'),lambda h:validate_headers(h,'pilot',expected,p)) as (a,d):
            for g in G:
                ensure(np.isfinite(a[g]).all() and np.isin(a[g+'_n'],[3,4]).all(),'FACE');ensure(not a[g][a[g+'_n']==3,3,:].view(np.uint64).any(),'PADDING');ensure(not np.bitwise_and(a[g+'_flags'],248).any(),'FACE');ensure(int(np.count_nonzero(a[g+'_flags']))==p['ambiguous_faces'][g],'COVERAGE')
                layer=[z for z in pilot_metadata[mi]['sections'] if (z['resolution']==3000000028082176.0)==g.startswith('road_')];ensure(len(layer)==1,'FACE')
                for fi,se in a[g+'_source_ids']:check_face(models[mi],layer[0]['lod'],int(se),int(fi))
            n,m=a['source_grid'].shape[:2];tri=a['source_triangles'];ensure(np.isfinite(a['source_grid']).all() and ((tri>=0)&(tri<n*m)).all(),'GRID');before=int(a['cap_before']);after=int(a['cap_after']);ensure(before in (0,8) and after in (0,8) and n-before-after>=2 and int(a['npz_start'])>=0,'GRID')
            cats=[]
            for i,t in enumerate(tri):
                rows=[int(v)//m for v in t];cols=[int(v)%m for v in t]
                for label,value in [('body_row_min',min(rows)),('body_row_max',max(rows)),('body_col_min',min(cols)),('body_col_max',max(cols))]:ensure(int(a[label][i])==value,'GRID')
                label_cat='CAP_START' if before and max(rows)<=before else 'CAP_END' if after and min(rows)>=n-after-1 else 'BODY';cats.append(label_cat);ensure(str(a['source_category'][i])==label_cat,'CATEGORY')
            categories=dict(Counter(cats));ensure(categories==p['source_regions'],'CATEGORY');ensure(sorted(map(int,a['bed_source_face']))==list(range(len(tri))),'GRID')
        del a
        actual={'model':p['model'],'model_index':mi,'instance_id':p['instance_id'],'site':p['site'],'archive':rel,'pose_row':int(loc[0]),'world_frame':'ALREADY_WORLD_UNCERTIFIED','arraydigestmap':d,'categories':categories,'historical_checks':p['checks']};ensure(IO.exact(bound[mi],actual))
    ensure(set(specs)=={i for i,x in cat.items() if x['group']=='custom_pilot'},'COVERAGE')
    for mi,row in rm.items():
        item=cat.get(mi);ensure(row['name']==(item['name'] if item else models[mi]['name']));ensure(row['group']==(item['group'] if item else 'proxy_only'));ensure(type(row['catalog_instance_count']) is int and row['catalog_instance_count']==(item['instances'] if item else 0));ensure(IO.exact(row['pose_rows'],np.flatnonzero(indices==mi).tolist()))
        kk={r['key'][3] for r in row['runs']};layers={'roadway':'RAW_UNCERTIFIED' if 0 in kk else 'NOT_SAVED','water_visual':'RAW_UNCERTIFIED' if 1 in kk else 'NOT_SAVED','conditional_proxy':'CONDITIONAL' if 2 in kk else 'NOT_SAVED','visual_bed':'ALREADY_WORLD_UNCERTIFIED' if mi in specs else 'NOT_SAVED'};ensure(IO.exact(row['layers'],layers))
    ensure(len(reader.records)==len(j)+len(archives) and len(archives)==expected['pilot_models']+3,'COVERAGE')
    coverage=dict(expected,npz_files=len(archives),npz_members=sum(len(x['members']) for x in reader.records if x['members'] is not None));ensure(IO.exact(report['coverage'],coverage));ensure(IO.exact(report['sources'],sorted(reader.records,key=lambda r:r['label'])))
    return {'status':'VERIFIED_SAVED_SCENE_INDEX_ONLY','contract_sha256':sha,'files_read':len(archives),'exposure_evaluated':False,'map_repaired':False}
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('contract');ap.add_argument('sha');ap.add_argument('report');ap.add_argument('output');x=ap.parse_args();out=Path(x.output);out.mkdir(exist_ok=False)
    try:
        c,s=IO.load_contract(x.contract,x.sha);report=IO.parse(IO.read_small(x.report,limit=33554432));IO.emit(out/'consumer.json',consume(c,s,x.sha,report))
    except Exception as e:IO.emit(out/'failure.json',{'status':'REJECTED','reason':getattr(e,'code','INTERNAL_ERROR'),'type':type(e).__name__,'detail':str(e)});raise
if __name__=='__main__':main()
