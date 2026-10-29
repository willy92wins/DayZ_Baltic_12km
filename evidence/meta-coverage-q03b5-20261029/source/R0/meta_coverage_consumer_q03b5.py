"""Separate scalar META35-offset walker; no producer imports or grouping."""
import sys,os,struct
sys.path.insert(0,os.path.dirname(__file__))
from pathlib import Path
import meta_coverage_io_q03b5 as I
LAYOUT=struct.Struct('<iiiiiBBBid')
def verify(cat,sections,raw,body):
    I.need(len(raw)%35==0 and LAYOUT.size==35,'SCHEMA')
    catalogs={};models={};roots=[]
    for index,item in enumerate(cat):
        key=item['index'];I.need(type(key) is int and key>=0 and key not in catalogs and type(item['name']) is str and type(item['group']) is str,'SCHEMA');catalogs[key]=(item['name'],item['group'],index)
        if item['group']!='vegetation_not_inspected':roots.append(key)
    for index,item in enumerate(sections):
        key=item['index'];I.need(type(key) is int and key>=0 and key not in models and type(item['name']) is str,'SCHEMA');models[key]=(item['name'],index)
        if key in catalogs:I.need(catalogs[key][0].replace('\\','/').strip('/').lower()==item['name'].replace('\\','/').strip('/').lower(),'IDENTITY')
    counts=[{},{}];by_group={};n=0
    for at in range(0,len(raw),35):
        row=LAYOUT.unpack_from(raw,at);mi,src=row[:2];key=(row[5],row[4],row[8]);n+=1
        bucket=by_group.setdefault(key,[0,{},{}]);bucket[0]+=1
        for role,value in enumerate((mi,src)):
            counts[role][value]=counts[role].get(value,0)+1;bucket[role+1][value]=bucket[role+1].get(value,0)+1
    I.need(type(body['rows']) is int and body['rows']==n,'REPORT')
    expected_roles={};anchors=[]
    for role,label in enumerate(('model','source_model')):
        expected=sorted(roots if role==0 else models);seen=sorted(counts[role]);missing=[i for i in expected if i not in counts[role]];unexpected=[i for i in seen if i not in expected]
        states=[]
        for value in sorted(set(expected+seen)):
            state='UNEXPECTED_META_ID' if value not in expected else 'NO_META_ROWS_IN_ROLE' if value not in counts[role] else 'OBSERVED_SAVED';states.append([value,state])
        expected_roles[label]={'expected':expected,'observed':seen,'missing':missing,'unexpected':unexpected,'equal':len(missing)==len(unexpected)==0,'counts':[[i,counts[role][i]] for i in seen],'states':states}
        for i in sorted(missing+unexpected):anchors.append([label,i,catalogs[i][2] if i in catalogs else None,models[i][1] if i in models else None])
    groups=[]
    for k,(total,mc,sc) in sorted(by_group.items()):groups.append({'key':list(k),'rows':total,'model':[[i,mc[i]] for i in sorted(mc)],'source_model':[[i,sc[i]] for i in sorted(sc)]})
    expected={'rows':n,'roles':expected_roles,'groups':groups,'catalog_map':[[i,*catalogs[i]] for i in sorted(catalogs)],'sections_map':[[i,*models[i]] for i in sorted(models)],'witness_anchors':anchors}
    I.need(I.same(body,expected),'REPORT')
def consume(c,digest,report):
    expected_keys={'schema','status','contract_sha256','claims','provenance','rows','roles','groups','catalog_map','sections_map','witness_anchors'}
    I.need(type(report) is dict and set(report)==expected_keys,'SCHEMA');I.need(report['schema']=='q03b5-report-v1' and report['status']=='META_COVERAGE_DIAGNOSTIC' and report['contract_sha256']==digest and I.same(report['claims'],c['claims']),'REPORT')
    with I.sources(c) as (cat,sections,r):
        raw=r['arrays']['meta.npy'].tobytes(order='C');I.need(len(raw)==35*c['rows'],'SCHEMA');I.need(I.sha(raw)==r['payloads']['meta.npy']['sha256'],'IDENTITY')
        I.need(I.same(report['provenance'],I.provenance(c,r)),'REPORT')
        verify(cat,sections,raw,{k:report[k] for k in ('rows','roles','groups','catalog_map','sections_map','witness_anchors')})
    return {'status':'VERIFIED_META_COVERAGE_DIAGNOSTIC','contract_sha256':digest,'rows':c['rows'],'cause':'NOT_ESTABLISHED','map_repaired':False}
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('contract');p.add_argument('sha');p.add_argument('report');p.add_argument('out');a=p.parse_args();out=Path(a.out);out.mkdir(exist_ok=False)
    try:
        c=I.load(a.contract,a.sha);p=Path(a.report);I.need(0<p.stat().st_size<=c['limits']['output'],'INPUT_CAP')
        with p.open('rb') as f:b=f.read(c['limits']['output']+1)
        I.need(len(b)<=c['limits']['output'],'INPUT_CAP');report=I.parse(b);I.emit(out/'consumer.json',consume(c,a.sha,report))
    except Exception as e:I.emit(out/'failure.json',{'status':'REJECTED','code':getattr(e,'code','IO_ERROR' if isinstance(e,OSError) else 'INTERNAL_ERROR'),'detail':str(e)});raise
if __name__=='__main__':main()
