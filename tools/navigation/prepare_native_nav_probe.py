"""Freeze native bridge and regional dry-point probes before querying the engine."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'evidence/regional-water/reference-v1.json'
reference = json.loads(source.read_text())
dry = [p for p in reference['samples'] if p['dry_interior']]
assert len(dry) == 751
target = ROOT / 'missions/BalticNativeNavV2.BalticTrial/init.c'
if target.exists():
    raise ValueError('Fresh probe required')
old = (ROOT / 'missions/BalticNav.BalticTrial/init.c').read_text()
query = old[old.index('static void BalticNavQuery'):old.index('static void BalticNavPaths')]
query = query.replace('step <= 60', 'step <= 120').replace('step / 60.0', 'step / 120.0')
center = (2417.14306640625, 6889.884765625)
axis = (.988364361, -.152104866)
def pos(distance):
    return f'"{center[0]+axis[0]*distance:.6f} 0 {center[1]+axis[1]*distance:.6f}"'
routes = [('west_local', -60, -50), ('east_local', 50, 60),
          ('west_east', -60, 60), ('east_west', 60, -60)]
body = '''// Temporary read-only server probe; no CE/actors or network state.
// AIWorld/PGFilter contracts: P:/scripts/3_game/ai/aiworld.c:80,111,137.
void main() { Print("BALTIC_NATIVE_NAV_MAIN_V1"); }
'''+query+'''
static void BalticNativeDryPoint(FileHandle report, int index, vector requested)
{
    AIWorld ai = GetGame().GetWorld().GetAIWorld();
    PGFilter walk = new PGFilter;
    walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
    requested[1] = GetGame().SurfaceY(requested[0], requested[2]);
    vector sampled;
    bool success = ai.SampleNavmeshPosition(requested, 2, walk, sampled);
    FPrintln(report, "D;" + index + ";" + requested + ";" + success + ";" + sampled);
}
'''
chunks = []
for start in range(0, len(dry), 32):
    name = f'BalticNativeDryChunk{start//32}'
    chunks.append(name)
    body += f'\nstatic void {name}(FileHandle report)\n{{\n'
    for i in range(start, min(start+32,len(dry))):
        p = dry[i]
        body += f'    BalticNativeDryPoint(report, {i}, "{p["x"]:.6f} 0 {p["z"]:.6f}");\n'
    body += '}\n'
body += '''
static void BalticNativeNav()
{
    if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
    FileHandle report = OpenFile("$profile:baltic_native_nav_v1.log", FileMode.WRITE);
    if (!report) return;
    FPrintln(report, "BALTIC_NATIVE_NAV_V1");
    FPrintln(report, "world=" + GetGame().GetWorldName());
    PGFilter walk = new PGFilter;
    walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
    FPrintln(report, "flags=" + walk.GetIncludeFlags() + ";" + walk.GetExcludeFlags());
'''
for label, start, finish in routes:
    body += f'    BalticNavQuery("{label}", {pos(start)}, {pos(finish)}, walk, report);\n'
body += f'''    PGFilter none = new PGFilter;
    none.SetFlags(PGPolyFlags.NONE, PGPolyFlags.ALL, PGPolyFlags.NONE);
    BalticNavQuery("negative_no_polygons", {pos(-60)}, {pos(60)}, none, report);
'''
for name in chunks:
    body += f'    {name}(report);\n'
body += '''    FPrintln(report, "BALTIC_NATIVE_NAV_COMPLETE");
    CloseFile(report);
    Print("BALTIC_NATIVE_NAV_COMPLETE_V1");
}
class BalticNativeNavMission: MissionServer
{
    override void OnInit()
    {
        super.OnInit();
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BalticNativeNav, 15000, false);
    }
    void ~BalticNativeNavMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BalticNativeNav);
    }
}
Mission CreateCustomMission(string path) { return new BalticNativeNavMission(); }
'''
target.parent.mkdir(parents=True)
target.write_text(body, encoding='utf-8')
manifest = {'status': 'FROZEN_BEFORE_RUNTIME', 'reference_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'mission_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'dry_points': dry,
            'routes': routes, 'bridge_center_xz': center, 'bridge_axis_xz': axis,
            'bridge_deck_y': 9, 'bridge_half_length': 37.5,
            'bridge_samples_per_direction': 121, 'roadway_nav_acceptance_m': .8,
            'regional_sample_radius_m': 2,
            'limits': ['Graph/sampling only. Not locomotion.', 'All 751 dry-reference points are retained; misses are reported, never selected away.']}
(ROOT / 'evidence/navigation/native-nav-reference-v2.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({'mission': str(target), 'dry_samples': len(dry), 'mission_sha256': manifest['mission_sha256']}))
