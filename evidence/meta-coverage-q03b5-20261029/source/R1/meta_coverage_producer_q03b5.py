"""NumPy grouping producer; diagnostics never repair equality."""
import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from pathlib import Path
import numpy as np
import meta_coverage_io_q03b5 as I
def maps(cat,sections):
    cm={};sm={};nonveg=set()
    for pos,row in enumerate(cat):
        i=row['index'];I.need(type(i) is int and i>=0 and i not in cm and type(row['name']) is str and type(row['group']) is str,'SCHEMA');cm[i]=[row['name'],row['group'],pos]
        if row['group']!='vegetation_not_inspected':nonveg.add(i)
    for pos,row in enumerate(sections):
        i=row['index'];I.need(type(i) is int and i>=0 and i not in sm and type(row['name']) is str,'SCHEMA');sm[i]=[row['name'],pos]
        if i in cm:I.need(cm[i][0].replace('\\','/').lower().strip('/')==row['name'].replace('\\','/').lower().strip('/'),'IDENTITY')
    return cm,sm,nonveg
def counts(column):
    ids,n=np.unique(column,return_counts=True);return [[int(i),int(v)] for i,v in zip(ids,n)]
def role(expected,pairs):
    observed={i for i,n in pairs};missing=expected-observed;extra=observed-expected
    return {'expected':sorted(expected),'observed':sorted(observed),'missing':sorted(missing),'unexpected':sorted(extra),'equal':not missing and not extra,'counts':pairs,'states':[[i,'UNEXPECTED_META_ID' if i in extra else 'NO_META_ROWS_IN_ROLE' if i in missing else 'OBSERVED_SAVED'] for i in sorted(expected|observed)]}
def derive(cat,sections,meta):
    cm,sm,roots=maps(cat,sections);roles={'model':role(roots,counts(meta['model'])),'source_model':role(set(sm),counts(meta['source_model']))};groups=[]
    triples=np.unique(meta[['kind','lod','proxy']])
    for q in triples:
        kind,lod,proxy=int(q['kind']),int(q['lod']),int(q['proxy']);chosen=(meta['kind']==kind)&(meta['lod']==lod)&(meta['proxy']==proxy)
        groups.append({'key':[kind,lod,proxy],'rows':int(chosen.sum()),'model':counts(meta['model'][chosen]),'source_model':counts(meta['source_model'][chosen])})
    groups.sort(key=lambda x:x['key']);I.need(sum(g['rows'] for g in groups)==len(meta),'SCHEMA')
    anchors=[]
    for label,r in roles.items():
        for i in sorted(r['missing']+r['unexpected']):anchors.append([label,i,cm[i][2] if i in cm else None,sm[i][1] if i in sm else None])
    return {'rows':len(meta),'roles':roles,'groups':groups,'catalog_map':[[i,*cm[i]] for i in sorted(cm)],'sections_map':[[i,*sm[i]] for i in sorted(sm)],'witness_anchors':anchors}
def produce(c,digest):
    with I.sources(c) as (cat,sections,r):
        meta=r['arrays']['meta.npy'];I.need(len(meta)==c['rows'],'SCHEMA');body=derive(cat,sections,meta);provenance=I.provenance(c,r)
    return {'schema':'q03b5-report-v1','status':'META_COVERAGE_DIAGNOSTIC','contract_sha256':digest,'claims':c['claims'],'provenance':provenance,**body}
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('contract');p.add_argument('sha');p.add_argument('out');a=p.parse_args();out=Path(a.out);out.mkdir(exist_ok=False)
    try:c=I.load(a.contract,a.sha);I.emit(out/'report.json',produce(c,a.sha),c['limits']['output'])
    except Exception as e:I.emit(out/'failure.json',{'status':'REJECTED','code':getattr(e,'code','IO_ERROR' if isinstance(e,OSError) else 'INTERNAL_ERROR'),'detail':str(e)});raise
if __name__=='__main__':main()
