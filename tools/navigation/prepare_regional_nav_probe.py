"""Freeze a server-only consumer probe before regional navigation is generated."""
import json
import numpy as np
from scipy.ndimage import distance_transform_edt
from prepare_regional_outline import ROOT, sha, save

ev = ROOT/'evidence/regional-outline-v3'
target = ROOT/'missions/BalticOutlineNavV3.BalticTrial/init.c'
if target.exists():
    raise ValueError('Fresh mission required')
reference = ROOT/'tests/regional_outline_v3/reference.npz'
if sha(reference) != 'b5ca00409f0814285c82a1fe6688fe49719574eadde415de08443ffedcbc574d':
    raise ValueError('Frozen candidate changed')
r = np.load(reference)
h = r['candidate']
land = (distance_transform_edt(~r['water'])*6 > 24) & (h >= 1.25)
points = []
seen = set()
def add(row, col, group):
    if (row,col) in seen:
        return
    seen.add((row,col))
    points.append(dict(index=len(points), x=int(col*6), z=int(12282-row*6),
                       y=float(h[row,col]), baseline_y=float(r['base'][row,col]), group=group))
for row in range(48,2000,96):
    for col in range(48,2000,96):
        if land[row,col]:
            group = 'reserve' if r['reserve'][row,col] else 'spb' if r['spb'][row,col] else 'regional'
            add(row,col,group)
routes=[]
for zone,(r0,r1,c0,c1) in enumerate([(350,900,600,1100),(1500,2000,400,1100),(900,1400,1400,1800)]):
    valid = land[r0:r1,c0:c1].copy()
    for j in range(2):
        weighted = np.where(valid,h[r0:r1,c0:c1],-9999)
        rr,cc=np.unravel_index(weighted.argmax(),weighted.shape)
        if weighted[rr,cc] < 5:
            break
        row,col=int(rr+r0),int(cc+c0)
        add(row,col,'summit_'+str(zone))
        # A short traverse entirely on the same summit, fixed before runtime.
        endcol=col+10
        if endcol<2048 and land[row,col:endcol+1].all():
            routes.append(dict(name=f'summit_{zone}_{j}',start=[col*6,float(h[row,col]),12282-row*6],
                               end=[endcol*6,float(h[row,endcol]),12282-row*6]))
        valid[max(0,rr-40):rr+41,max(0,cc-40):cc+41]=False

code='''// Temporary server-only probe, no RPC, economy or actors.
// Verified local contracts: scripts/3_game/ai/aiworld.c:80,111,137;
// global/game.c:930,1162; global/world.c:119; 1_core/proto/ensystem.c:417,443,481.
void main() { Print("BALTIC_OUTLINE_NAV_MAIN_V3"); }
static void BalticOutlinePoint(FileHandle f, int index, vector requested, PGFilter filter)
{
    requested[1] = GetGame().SurfaceY(requested[0], requested[2]);
    vector sampled;
    bool ok = GetGame().GetWorld().GetAIWorld().SampleNavmeshPosition(requested, 2, filter, sampled);
    FPrintln(f, "D;" + index + ";" + requested + ";" + ok + ";" + sampled);
}
static void BalticOutlinePath(FileHandle f, string name, vector start, vector finish, PGFilter filter)
{
    AIWorld ai = GetGame().GetWorld().GetAIWorld();
    start[1] = GetGame().SurfaceY(start[0], start[2]);
    finish[1] = GetGame().SurfaceY(finish[0], finish[2]);
    vector a, b;
    bool sa = ai.SampleNavmeshPosition(start, 2, filter, a);
    bool sb = ai.SampleNavmeshPosition(finish, 2, filter, b);
    TVectorArray path = new TVectorArray;
    bool found = false;
    if (sa && sb) found = ai.FindPath(a, b, filter, path);
    FPrintln(f, "Q;" + name + ";" + sa + ";" + sb + ";" + found + ";" + path.Count());
    for (int i=0; i<path.Count(); i++) FPrintln(f, "P;" + name + ";" + i + ";" + path[i]);
}
'''
chunks=[]
for start in range(0,len(points),32):
    name='BalticOutlineChunk'+str(start//32)
    chunks.append(name)
    code+=f'\nstatic void {name}(FileHandle f, PGFilter filter)\n{{\n'
    for pt in points[start:start+32]:
        code+=f'    BalticOutlinePoint(f, {pt["index"]}, "{pt["x"]} 0 {pt["z"]}", filter);\n'
    code+='}\n'
code+='''
static void BalticOutlineProbe()
{
    if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
    FileHandle f = OpenFile("$profile:baltic_outline_nav_v3.log", FileMode.WRITE);
    if (!f) return;
    FPrintln(f, "BALTIC_OUTLINE_NAV_V3");
    FPrintln(f, "world=" + GetGame().GetWorldName());
    PGFilter walk = new PGFilter;
    walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
    FPrintln(f, "flags=" + walk.GetIncludeFlags() + ";" + walk.GetExcludeFlags());
'''
for name in chunks:
    code+=f'    {name}(f, walk);\n'
for route in routes:
    a,b=route['start'],route['end']
    code+=f'    BalticOutlinePath(f, "{route["name"]}", "{a[0]} 0 {a[2]}", "{b[0]} 0 {b[2]}", walk);\n'
code+='''    PGFilter none = new PGFilter;
    none.SetFlags(PGPolyFlags.NONE, PGPolyFlags.ALL, PGPolyFlags.NONE);
    BalticOutlinePath(f, "negative", "6000 0 6000", "6060 0 6000", none);
    FPrintln(f, "BALTIC_OUTLINE_NAV_COMPLETE");
    CloseFile(f);
    Print("BALTIC_OUTLINE_NAV_COMPLETE_V3");
}
class BalticOutlineNavMission: MissionServer
{
    override void OnInit()
    {
        super.OnInit();
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BalticOutlineProbe, 15000, false);
    }
    void ~BalticOutlineNavMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BalticOutlineProbe);
    }
}
Mission CreateCustomMission(string path) { return new BalticOutlineNavMission(); }
'''
target.parent.mkdir(parents=True)
target.write_text(code,encoding='utf-8',newline='\n')
save(ev/'nav-probe-reference.json',dict(status='FROZEN_BEFORE_RUNTIME',points=points,routes=routes,
     candidate_sha256=sha(reference),mission_sha256=sha(target),height_tolerance_m=.06,
     sample_radius_m=2,path_max_length_factor=3,
     limits=['No physical actor traversal, no 80-100 player proof.', 'Every fixed point retained, misses fail coverage.']))
print(json.dumps(dict(points=len(points),routes=len(routes),mission=str(target))))
