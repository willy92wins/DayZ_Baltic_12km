"""Semantic producer: sequential META runs, then pose and pilot bindings."""
import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from pathlib import Path
from collections import Counter
import numpy as np
import saved_scene_io_q03b4 as I
R=I.require
GROUPS=('bed','water','unknown','road_bed','road_water','road_unknown')
EXTRAS=('source_grid','source_triangles','body_row_min','body_row_max','body_col_min','body_col_max','source_category','bed_source_face','npz_start','cap_before','cap_after')
META=[['model','<i4'],['source_model','<i4'],['face','<i4'],['section','<i4'],['lod','<i4'],['kind','|u1'],['vertices','|u1'],['flags','|u1'],['proxy','<i4'],['planarity_m','<f8']]
def norm(x):
    R(type(x) is str and x.isascii() and not any(ord(c)<32 for c in x) and ':' not in x,'SCHEMA','name')
    x=x.replace('\\','/').lower().strip('/');R(x and all(p not in ('','.','..') for p in x.split('/')),'SCHEMA','name');return x
def integer(x):R(type(x) is int and x>=0,'SCHEMA','integer');return x
def shape_rules(s,kind,e,spec=None):
    def check(n,types,shape=None):
        v=s[n+'.npy'];R(v['dtype'] in types and (shape is None or v['shape']==shape),'SCHEMA',n)
    if kind=='prototypes':
        check('vertices',['<f8'],[e['prototype_faces'],4,3]);check('meta',[META],[e['prototype_faces']])
    elif kind in ('instances','selected'):
        for n in ('ids','model_index'):check(n,['<i4','<i8','<u4','<u8'],[e['instances']])
        check('matrix',['<f4','<f8'],[e['instances'],12])
        if kind=='instances':
            for n in ('norm','determinant','nonorthogonality'):check(n,['<f8'],[e['instances'],3] if n=='norm' else [e['instances']])
    else:
        for n in GROUPS:
            f=spec['faces'][n];check(n,['<f8'],[f,4,3]);check(n+'_n',['|u1'],[f]);check(n+'_flags',['|u1'],[f]);check(n+'_source_ids',['<i4'],[f,2])
        b=spec['faces']['bed'];check('source_grid',['<f8']);g=s['source_grid.npy']['shape']
        R(len(g)==3 and g[2]==3 and g[0]>=2 and g[1]>=2 and g[0]*g[1]<=3*b,'GRID')
        check('source_triangles',['<i4','<i8'],[b,3])
        for n in ('body_row_min','body_row_max','body_col_min','body_col_max'):check(n,['<i4','<i8'],[b])
        check('source_category',['<U9'],[b]);check('bed_source_face',['<i4'],[b])
        for n in ('npz_start','cap_before','cap_after'):check(n,['<i4'],[])
def names(kind):
    if kind=='prototypes':return ['vertices','meta']
    if kind=='selected':return ['ids','model_index','matrix']
    if kind=='instances':return ['ids','model_index','matrix','norm','determinant','nonorthogonality']
    return [x+t for x in GROUPS for t in ('','_n','_flags','_source_ids')]+list(EXTRAS)
def index_sections(rows):
    table={};canon=set()
    for row in rows:
        I.keys(row,['name','index','center','lods','proxies']);idx=integer(row['index']);n=norm(row['name'])
        R(idx not in table and n not in canon,'IDENTITY');canon.add(n);table[idx]=row
        R(len(row['center'])==3 and all(type(x) in (int,float) and np.isfinite(x) for x in row['center']),'SCHEMA')
        lods=set()
        for lod in row['lods']:
            I.keys(lod,['index','resolution','faces','sections']);li=integer(lod['index']);R(li not in lods,'IDENTITY');lods.add(li)
            R(type(lod['resolution']) in (float,int) and np.isfinite(lod['resolution']),'SCHEMA');integer(lod['faces']);ss=set()
            for s in lod['sections']:
                I.keys(s,['index','faces','material','material_raw','texture','texture_raw']);si=integer(s['index']);R(si not in ss,'IDENTITY');ss.add(si);integer(s['faces'])
                R(all(type(s[k]) is str for k in ('material','material_raw','texture','texture_raw')),'SCHEMA')
            R(sum(s['faces'] for s in lod['sections'])==lod['faces'],'FACE')
        for p in row['proxies']:
            I.keys(p,['model','matrix']);norm(p['model']);R(len(p['matrix'])==12 and all(type(x) in (int,float) and np.isfinite(x) for x in p['matrix']),'SCHEMA')
    return table
def routes_check(routes,models):
    lookup={norm(m['name']):i for i,m in models.items()}
    for route in routes:
        I.keys(route,['root_model','slots','source_model']);at=integer(route['root_model']);integer(route['source_model']);seen={at}
        R(type(route['slots']) is list and 0<len(route['slots'])<=16,'PROXY')
        for pair in route['slots']:
            R(type(pair) is list and len(pair)==2 and all(type(x) is int for x in pair),'SCHEMA');parent,slot=pair
            R(parent==at and at in models and 0<=slot<len(models[at]['proxies']),'PROXY')
            child=lookup.get(norm(models[at]['proxies'][slot]['model']));R(child is not None and child not in seen,'PROXY');seen.add(child);at=child
        R(at==route['source_model'],'PROXY')
def face_check(model,lod,section,face,kind=None):
    ls={x['index']:x for x in model['lods']};R(lod in ls,'FACE');l=ls[lod];ss={s['index']:s for s in l['sections']}
    R(0<=face<l['faces'] and section in ss,'FACE')
    if kind==0:R(l['resolution']==3000000028082176.0,'FACE')
    if kind in (1,2):
        visual=[q for q in model['lods'] if 0<=q['resolution']<1000];R(visual,'FACE')
        v=min(x['resolution'] for x in visual);R(sum(x['resolution']==v for x in visual)==1 and l['resolution']==v,'FACE')
        R(ss[section]['material'] in ('dz/water/streams/data/water_streambed.rvmat','dz/water/ponds/data/pond_moss_1.rvmat'),'FACE')
def padding(v,n):
    R(np.isfinite(v).all() and np.isin(n,[3,4]).all(),'FACE')
    R(not v[n==3,3,:].view(np.uint64).any(),'PADDING')
def pilot_check(a,spec,metadata,models):
    for g in GROUPS:
        padding(a[g],a[g+'_n']);R(((a[g+'_flags']&~np.uint8(7))==0).all(),'FACE')
        R(int((a[g+'_flags']!=0).sum())==spec['ambiguous_faces'][g],'COVERAGE')
        lods=metadata['sections'];layer=[x for x in lods if (x['resolution']==3000000028082176.0)==g.startswith('road_')]
        R(len(layer)==1,'FACE');lo=layer[0]['lod']
        for face,section in a[g+'_source_ids']:face_check(models[spec['model_index']],lo,int(section),int(face))
    grid=a['source_grid'];tri=a['source_triangles'];n,m=grid.shape[:2];b=len(tri)
    R(np.isfinite(grid).all() and ((tri>=0)&(tri<n*m)).all(),'GRID')
    for name,expected in [('body_row_min',(tri//m).min(1)),('body_row_max',(tri//m).max(1)),('body_col_min',(tri%m).min(1)),('body_col_max',(tri%m).max(1))]:R(np.array_equal(a[name],expected),'GRID')
    before=int(a['cap_before']);after=int(a['cap_after']);R(before in (0,8) and after in (0,8) and n-before-after>=2 and int(a['npz_start'])>=0,'GRID')
    expected=np.full(b,'BODY',dtype='<U9')
    if after:expected[(tri//m).min(1)>=n-after-1]='CAP_END'
    if before:expected[(tri//m).max(1)<=before]='CAP_START'
    R(np.array_equal(a['source_category'],expected),'CATEGORY')
    counts=dict(Counter(a['source_category'].tolist()));R(counts==spec['source_regions'],'CATEGORY')
    R(np.array_equal(np.sort(a['bed_source_face']),np.arange(b)),'GRID')
    return counts
def epoch(c,s,j):
    root=Path(s['source_root']);old=j['deployed-surface-prototypes-20261028/inputs.json'];new=j['pilot-visible-surface-extraction-20261028/inputs.json'];pins=old['source_pins']
    eq={str(root/'package-kit7-fc-world-20261026/compiled/narva_trial/baltic_trial.wrp'):s['epoch']['wrp_compiled'],str(root/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'):s['epoch']['wrp_editable'],r'P:\Mods\@DayZ_Baltic_EV112_Kit7Nav8Load1\Addons\baltic_stream_pilot.pbo':s['epoch']['pilot_pbo']}
    R(all(pins.get(k)==v for k,v in eq.items()),'EPOCH')
    surface=s['pins']['deployed-surface-prototypes-20261028/inputs.json'];inst=next(x for x in s['arrays'] if x['kind']=='instances');selected=next(x for x in s['arrays'] if x['kind']=='selected')
    R(new['pins'].get(surface['path'])==surface['sha256'] and new['pins'].get(inst['path'])==inst['sha256'] and pins.get(selected['path'])==selected['sha256'],'EPOCH')
    for spec in s['arrays']:
        manifest=j['pilot_manifest'] if spec['kind']=='pilot' else j['surface_manifest'] if spec['kind']!='selected' else old['discovery_artifacts']
        rel=spec['relative'];entry=manifest.get(rel);R(type(entry) is dict and entry.get('sha256')==spec['sha256'] and entry.get('bytes')==spec['bytes'],'EPOCH')
def produce(c,s,contract_sha):
    reader=I.Reader(c);j={k:reader.json(k,p) for k,p in s['pins'].items()};e=s['expected'];epoch(c,s,j)
    catalog=j['deployed-surface-prototypes-20261028/model-catalog.json'];models=index_sections(j['deployed-surface-prototypes-20261028/model-sections.json']);routes=j['deployed-surface-prototypes-20261028/proxy-paths.json'];routes_check(routes,models)
    cat={};ns=set()
    for m in catalog:
        I.keys(m,['index','name','instances','group']);i=integer(m['index']);n=norm(m['name']);integer(m['instances']);R(type(m['group']) is str and i not in cat and n not in ns,'IDENTITY');cat[i]=m;ns.add(n)
    nonveg={i for i,v in cat.items() if v['group']!='vegetation_not_inspected'};proxy=set(models)-set(cat)
    R(len(cat)==e['source_models'] and len(set(cat)-nonveg)==e['vegetation_models_not_saved'] and len(models)==e['prototype_models'] and len(proxy)==e['proxy_only_models'],'COVERAGE')
    R(nonveg<=set(models) and all(norm(models[i]['name'])==norm(cat[i]['name']) for i in nonveg),'IDENTITY')
    R(len(routes)==e['proxy_paths'],'COVERAGE')
    lookup={x['kind']:x for x in s['arrays'] if x['kind']!='pilot'};R(set(lookup)=={'prototypes','selected','instances'},'COVERAGE')
    runs=[];count=Counter();source_set=set();model_set=set()
    with reader.open(lookup['prototypes'],names('prototypes'),lambda x:shape_rules(x,'prototypes',e)) as (a,d):
        meta=a['meta'];padding(a['vertices'],meta['vertices']);R(np.isfinite(meta['planarity_m']).all() and (meta['planarity_m']>=0).all(),'FACE')
        for pos,row in enumerate(meta):
            mi,src,lo,kind,pr=map(int,[row['model'],row['source_model'],row['lod'],row['kind'],row['proxy']]);source_set.add(src);model_set.add(mi)
            R(mi in nonveg and src in models and kind in (0,1,2),'FACE');face_check(models[src],lo,int(row['section']),int(row['face']),kind)
            R(int(row['flags'])&~7==0,'FACE')
            if kind==2:R(0<=pr<len(routes) and routes[pr]['root_model']==mi and routes[pr]['source_model']==src and int(row['flags'])&1,'PROXY')
            else:R(pr==-1 and src==mi and not int(row['flags'])&1,'PROXY')
            key=[mi,src,lo,kind,pr]
            if runs and runs[-1]['key']==key:runs[-1]['end']=pos+1
            else:runs.append({'key':key,'start':pos,'end':pos+1})
            count[kind]+=1;count['ambiguous']+=bool(int(row['flags'])&2);count['degenerate']+=bool(int(row['flags'])&4)
        R(model_set==nonveg and source_set==set(models),'COVERAGE')
    del a
    for k,label in [(0,'roadway'),(1,'water_visual'),(2,'conditional_proxy'),('ambiguous','ambiguous'),('degenerate','degenerate')]:R(count[k]==e[label],'COVERAGE')
    with reader.open(lookup['selected'],names('selected'),lambda x:shape_rules(x,'selected',e)) as (a,selected_desc):pass
    del a
    poses={}
    with reader.open(lookup['instances'],names('instances'),lambda x:shape_rules(x,'instances',e)) as (a,d):
        R(all(I.exact(d[k+'.npy'],selected_desc[k+'.npy']) for k in ('ids','model_index','matrix')),'POSE')
        R(len(np.unique(a['ids']))==e['instances'] and all(np.isfinite(a[k]).all() for k in ('matrix','norm','determinant','nonorthogonality')),'POSE')
        for ix,(id,mi) in enumerate(zip(a['ids'],a['model_index'])):poses.setdefault(int(mi),[]).append([ix,int(id)])
        R({k:len(v) for k,v in poses.items()}=={i:cat[i]['instances'] for i in nonveg},'POSE')
    del a
    specs=s['pilot_specs'];metas=j['pilot-visible-surface-extraction-20261028/models.json'];pm={x['model_index']:x for x in metas};pilots=[];used=set()
    R(len(specs)==len(pm)==e['pilot_models'],'COVERAGE')
    for sp in specs:
        mi=sp['model_index'];R(mi not in used and mi in pm and mi in cat,'POSE');used.add(mi)
        R(norm(sp['model'])==norm(cat[mi]['name']) and poses.get(mi) and len(poses[mi])==1 and poses[mi][0][1]==sp['instance_id'],'POSE')
        R(all(I.exact(pm[mi][k],v) for k,v in sp.items()),'IDENTITY','pilot metadata')
        archive=next((x for x in s['arrays'] if x['kind']=='pilot' and x['relative']=='pilot-visible-surface-extraction-20261028/'+sp['file']),None);R(archive is not None and pm[mi]['sha256']==archive['sha256'],'COVERAGE')
        with reader.open(archive,names('pilot'),lambda x:shape_rules(x,'pilot',e,sp)) as (a,d):categories=pilot_check(a,sp,pm[mi],models)
        del a
        pilots.append({'model':sp['model'],'model_index':mi,'instance_id':sp['instance_id'],'site':sp['site'],'archive':archive['relative'],'pose_row':poses[mi][0][0],'world_frame':'ALREADY_WORLD_UNCERTIFIED','arraydigestmap':d,'categories':categories,'historical_checks':sp['checks']})
    R(used=={i for i,m in cat.items() if m['group']=='custom_pilot'},'COVERAGE')
    R(len(s['arrays'])==len(reader.records)-len(j)==e['pilot_models']+3,'COVERAGE')
    result=[]
    for i in sorted(set(cat)|proxy):
        m=cat[i] if i in cat else {'name':models[i]['name'],'group':'proxy_only','instances':0};rr=[r for r in runs if r['key'][0]==i];kinds={r['key'][3] for r in rr}
        result.append({'index':i,'name':m['name'],'group':m['group'],'catalog_instance_count':m['instances'],'pose_rows':[v[0] for v in poses.get(i,[])],'runs':rr,'layers':{'roadway':'RAW_UNCERTIFIED' if 0 in kinds else 'NOT_SAVED','water_visual':'RAW_UNCERTIFIED' if 1 in kinds else 'NOT_SAVED','conditional_proxy':'CONDITIONAL' if 2 in kinds else 'NOT_SAVED','visual_bed':'ALREADY_WORLD_UNCERTIFIED' if i in used else 'NOT_SAVED'}})
    coverage=dict(e,npz_files=len(s['arrays']),npz_members=sum(len(r['members']) for r in reader.records if r['members'] is not None))
    return {'schema':'q03b4-report-v1','contract_sha256':contract_sha,'status':c['status'],'claims':s['claims'],'coverage':coverage,'sources':sorted(reader.records,key=lambda r:r['label']),'models':result,'pilots':sorted(pilots,key=lambda p:p['model_index']),'proxy_routes':routes,'limitations':c['historical_claims']}
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('contract');ap.add_argument('sha');ap.add_argument('output');args=ap.parse_args()
    out=Path(args.output);out.mkdir(exist_ok=False)
    try:
        c,s=I.load_contract(args.contract,args.sha);I.emit(out/'report.json',produce(c,s,args.sha))
    except Exception as ex:
        I.emit(out/'failure.json',{'status':'REJECTED','reason':getattr(ex,'code','INTERNAL_ERROR'),'type':type(ex).__name__,'detail':str(ex)});raise
if __name__=='__main__':main()
