"""Stage the same fixed scene with read-only native height probes for all A/B/A phases."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parent
SOURCE=Path(r'C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticRenderLayerProbeV1.BalticTrial/init.c')
DEST=SOURCE.parent.parent/'BalticUnderlayDiagnosticV1.BalticTrial'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    if DEST.exists():raise FileExistsError(DEST)
    text=SOURCE.read_text(encoding='utf-8-sig')
    text=text.replace('BalticRenderLayerProbeV1Mission','BalticUnderlayDiagnosticV1Mission')
    text=text.replace('baltic_render_layer_v1.log','baltic_underlay_scene_v1.log')
    anchor='        m_NextMs = GetGame().GetTime() + 5000;'
    if text.count(anchor)!=1:raise ValueError('OnInit anchor changed')
    text=text.replace(anchor,anchor+'\n        DumpUnderlayHeights();')
    anchor='    string WaterAt(float x, float z)'
    if text.count(anchor)!=1:raise ValueError('Method anchor changed')
    function='''    // Native signature: scripts/3_game/global/game.c:1162 SurfaceY(float,float).
    void DumpUnderlayHeights()
    {
        FileHandle file = OpenFile("$profile:baltic_underlay_heights_v1.log", FileMode.WRITE);
        if (!file) return;
        FPrintln(file, "BEGIN;35;35");
        int count = 0;
        for (int r = 863; r <= 897; r++)
        {
            for (int c = 383; c <= 417; c++)
            {
                float x = 6.0 * c;
                float z = 12282.0 - 6.0 * r;
                float y = GetGame().SurfaceY(x, z);
                string row = "H;" + r + ";" + c;
                row = row + ";" + y.ToString();
                FPrintln(file, row);
                count++;
            }
        }
        FPrintln(file, "END;" + count);
        CloseFile(file);
    }

'''
    text=text.replace(anchor,function+anchor)
    local=ROOT/'runtime-mission';local.mkdir(exist_ok=False)
    (local/'init.c').write_text(text,encoding='utf-8')
    DEST.mkdir(exist_ok=False)
    shutil.copyfile(local/'init.c',DEST/'init.c')
    if sha(local/'init.c')!=sha(DEST/'init.c'):raise ValueError('Mission copy mismatch')
    (ROOT/'runtime-mission.json').write_text(json.dumps({'source':str(SOURCE),'source_sha256':sha(SOURCE),
        'mission':str(DEST),'init_sha256':sha(DEST/'init.c'),'native_probe_vertices':1225,
        'same_mission_all_phases':True,'mutable_terrain':False,
        'liveness_control':'Before each phase translate fixed camera+10m X, capture, restore, capture. Require measurable 3D bridge displacement and exact restored matrix; static low-delta warning alone is not a failed liveness gate (mcp_capture.py:817-828). Then 3 target captures with per-capture readback. No acceptance without reproduced gray ROI in A and A-prime.'},indent=2)+'\n')
    print(sha(DEST/'init.c'))

if __name__=='__main__':main()
