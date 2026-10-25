"""Freeze engine readback points and a bounded three-site visual fixture."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import shapely
from shapely.geometry import shape
R=Path('P:/DayZ_Baltic_12km_dev');E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/terrain'))
from v30_common import cell_planes,tri_sample
from audit_fairway_triangles_v30 import records,save,sha
source=R/'missions/BalticV30ShoreCompareV1.BalticTrial/init.c'
dest=R/'missions/BalticV30DeltaV1.BalticTrial'
assert not dest.exists()
t=np.load('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz');h=t['heights'].astype(float)
plane=cell_planes(t['cls'],t['level'])
fc=json.loads((E/'axes-corridors.geojson').read_text())['features']
pts=np.concatenate([records(shape(f['geometry']),plane)['xz'] for f in fc if f['properties']['kind']=='corridor24m'])
pts=np.unique(np.round(pts,5),axis=0)
assert np.max(tri_sample(h,pts[:,0],pts[:,1]))<=-2.49
# Dry references are selected before running, on unchanged island/road cores.
dry=np.array([[8364.,10200.],[8346.,10294.],[8484.,10140.],[8694.,10270.]])
q=np.vstack([pts,dry]);hh=tri_sample(h,q[:,0],q[:,1]);expected=['water']*len(pts)+['dry']*len(dry)
refs=[dict(id=i,kind=k,x=float(x),z=float(z),expected_ground_m=float(y)) for i,((x,z),y,k) in enumerate(zip(q,hh,expected))]
text=source.read_text().replace('BalticV30ShoreCompareMission','BalticV30DeltaMission').replace('baltic_v30_shore_compare_v1.log','baltic_v30_delta_v1.log').replace('BALTIC_V30_SHORE_COMPARE_V1','BALTIC_V30_DELTA_V1').replace('Count() == 2','Count() == 3').replace('END;2','END;3').replace('pos = "5142 0 1086"','pos = "8346 0 10294"')
text=text.replace('    protected bool m_BalticComplete;','''    protected bool m_BalticComplete;
    protected ref array<string> m_BalticQueries = new array<string>;
    protected int m_BalticQueryIndex;
    protected bool m_BalticQueriesDone;''')
anchor='        m_BalticReady = m_BalticSites.Count() == 3;'
replacement='''        FileHandle queries = OpenFile("$mission:queries.csv", FileMode.READ);
        if (!queries) return;
        while (FGets(queries, row) >= 0)
        {
            if (row == "") continue;
            fields.Clear(); row.Split(";", fields);
            if (fields.Count() != 2) { CloseFile(queries); LogTour("FAIL;QUERY_SCHEMA"); return; }
            m_BalticQueries.Insert(row);
        }
        CloseFile(queries);
        LogTour("QBEGIN;" + m_BalticQueries.Count());
        m_BalticReady = m_BalticSites.Count() == 3 && m_BalticQueries.Count() == QUERY_COUNT;'''.replace('QUERY_COUNT',str(len(q)))
assert text.count(anchor)==1;text=text.replace(anchor,replacement)
anchor='    override void OnUpdate(float timeslice)'
method='''    void ReadQueryBatch()
    {
        if (m_BalticQueriesDone) return;
        for (int batch = 0; batch < 16 && m_BalticQueryIndex < m_BalticQueries.Count(); batch++)
        {
            array<string> parts = new array<string>;
            m_BalticQueries[m_BalticQueryIndex].Split(";", parts);
            vector pos = parts[1].ToVector();
            float ground = GetGame().SurfaceY(pos[0], pos[2]);
            bool sea = GetGame().SurfaceIsSea(pos[0], pos[2]);
            bool pond = GetGame().SurfaceIsPond(pos[0], pos[2]);
            float noWave = GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(pos[0], ground + 100, pos[2]));
            float depth = GetGame().GetWaterDepth(Vector(pos[0], ground + 0.01, pos[2]));
            LogTour("Q;" + parts[0] + ";" + ground + ";" + sea + ";" + pond + ";" + noWave + ";" + depth + ";" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax());
            m_BalticQueryIndex++;
        }
        if (m_BalticQueryIndex == m_BalticQueries.Count())
        {
            m_BalticQueriesDone = true;
            LogTour("QEND;" + m_BalticQueryIndex);
        }
    }

'''
assert text.count(anchor)==1;text=text.replace(anchor,method+anchor)
anchor='        if (!player) return;';assert text.count(anchor)==1;text=text.replace(anchor,anchor+'\n        ReadQueryBatch();')
dest.mkdir()
(dest/'init.c').write_text(text,encoding='utf-8',newline='\n')
(dest/'sites.csv').write_text('little_mouth;8346 0 10294;0 0 0;8370 0 10326;8370 0 10326\ngreat_neva;8484 0 10140;90 0 0;8514 0 10140;8514 0 10140\nneva_join;8694 0 10270;-144 0 0;8676 0 10230;8682 0 10218\n',encoding='ascii',newline='\n')
(dest/'queries.csv').write_text(''.join(f'{i};{x:.5f} 0 {z:.5f}\n' for i,(x,z) in enumerate(q)),encoding='ascii',newline='\n')
save(E/'runtime-reference.json',dict(status='FROZEN_BEFORE_RUN',terrain_sha256=sha(Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')),
 query_count=len(q),water_count=len(pts),dry_count=len(dry),points=refs,
 limits=dict(height_error_m=.02,nominal_min_depth_m=2.99,sea_min_m=.5,sea_max_m=1.,dry_freeboard_m=.25),
 provenance={str(p):sha(p) for p in [source,*(dest/name for name in ('init.c','sites.csv','queries.csv'))]},
 scope='Native triangle/corridor vertices rounded to 1e-5 m, plus four unchanged dry controls. Diagnostic engine queries, not boat traversal.'))
print(json.dumps(dict(mission=str(dest),queries=len(q),water=len(pts),dry=len(dry))))
