"""Add engine frame captures and client-native counters to the frozen twelve-view tour."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parent = ROOT/'evidence/overnight-2026-10-01/foundation-visual-v1/reference.json'
    ref = json.loads(parent.read_text())
    source = ROOT/'packages/foundation-visual-v1/baltic_foundation_visual/scripts/5_Mission/BalticRenderProbe.c'
    assert sha(source) == ref['script_sha256']
    ev = ROOT/'evidence/overnight-2026-10-01/foundation-visual-v2'
    out = ROOT/'packages/foundation-visual-v2'
    mission = ROOT/'missions/BalticFoundationVisualV2.BalticTrial'
    destination = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    mod = Path('P:/Mods/@BalticFoundationVisualV2')
    for path in (ev, out, mission, destination, mod):
        if path.exists():
            raise ValueError('Fresh output required: '+str(path))
    code = source.read_text().replace('visual_v1', 'visual_v2').replace('VISUAL_V1', 'VISUAL_V2')
    anchor = '    protected float m_BalticCameraOldNear;'
    assert code.count(anchor) == 1
    code = code.replace(anchor, anchor+'''
    protected float m_BalticMetricsNext;
    protected int m_BalticCapturePhase = -1;
''')
    anchor = '        if (m_BalticRenderNextRecord > 0'
    assert code.count(anchor) == 1
    code = code.replace(anchor, '        BalticVisualMetrics();\n\n'+anchor)
    anchor = '    protected void BalticRenderPose('
    method = '''    protected void BalticVisualMetrics()
    {
        if (m_BalticRenderPhase < 0 || m_BalticRenderPhase >= 12) return;
        float phaseStart = 15 + 45 * m_BalticRenderPhase;
        float phaseElapsed = m_BalticRenderTime - phaseStart;
        if (m_BalticCapturePhase < m_BalticRenderPhase && phaseElapsed >= 25)
        {
            string name = "$profile:baltic_foundation_visual_v2_" + m_BalticRenderPhase + ".dds";
            MakeScreenshot(name);
            m_BalticCapturePhase = m_BalticRenderPhase;
            BalticRenderRecord("CAPTURE_REQUEST_" + m_BalticRenderPhase, false);
        }
        if (phaseElapsed < 10 || phaseElapsed > 40 || m_BalticRenderTime < m_BalticMetricsNext) return;
        m_BalticMetricsNext = m_BalticRenderTime + 1;
        FileHandle f = OpenFile("$profile:baltic_foundation_client_metrics_v2.log", FileMode.APPEND);
        if (!f) return;
        string row = "F;" + m_BalticRenderPhase + ";" + m_BalticRenderTime + ";" + GetGame().GetTickTime();
        row = row + ";" + GetGame().GetLastFPS() + ";" + GetGame().GetAvgFPS(64);
        row = row + ";" + GetGame().GetMinFPS(64) + ";" + GetGame().GetMaxFPS(64) + ";" + GetFPS();
        row = row + ";" + GetGame().GetCurrentCameraPosition().ToString();
        FPrintln(f, row);
        CloseFile(f);
    }

'''
    assert code.count(anchor) == 1
    code = code.replace(anchor, method+anchor)
    anchor = '        BalticRenderRecord("START", true);'
    code = code.replace(anchor, '''        FileHandle metrics = OpenFile("$profile:baltic_foundation_client_metrics_v2.log", FileMode.WRITE);
        if (metrics) { FPrintln(metrics,"BALTIC_FOUNDATION_CLIENT_METRICS_V2"); CloseFile(metrics); }
'''+anchor)
    anchor = '        FPrintln(report, "original_near_plane=" + m_BalticCameraOldNear);'
    code = code.replace(anchor, '''        if (camera)
        {
            FPrintln(report,"camera_native_position=" + camera.GetPosition().ToString());
            FPrintln(report,"camera_native_orientation=" + camera.GetOrientation().ToString());
            FPrintln(report,"camera_active=" + camera.IsActive());
            FPrintln(report,"camera_frozen=" + camera.IsFreezed());
        }
        FPrintln(report,"current_fov=" + Camera.GetCurrentFOV());
        FPrintln(report,"saved_position=" + m_BalticCameraOldPosition.ToString());
        FPrintln(report,"saved_orientation=" + m_BalticCameraOldOrientation.ToString());
        FPrintln(report,"saved_active=" + m_BalticCameraWasActive);
        FPrintln(report,"saved_frozen=" + m_BalticCameraWasFrozen);
        FPrintln(report,"saved_fov=" + m_BalticCameraOldFOV);
'''+anchor)
    prefix = 'baltic_foundation_visual_v2'
    stage = out/prefix
    (stage/'scripts/5_Mission').mkdir(parents=True)
    ev.mkdir(parents=True)
    mission.mkdir()
    script = stage/'scripts/5_Mission/BalticRenderProbe.c'
    script.write_text(code)
    config = (ROOT/'packages/foundation-visual-v1/config.cpp').read_text().replace('baltic_foundation_visual',prefix)
    (out/'config.cpp').write_text(config)
    addons = out/'Addons'
    addons.mkdir()
    shutil.copy2(ROOT/'missions/BalticFoundationVisualV1.BalticTrial/init.c', mission/'init.c')
    tools = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    for index, args in enumerate([[tools/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',out/'config.cpp'],
                                  [tools/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]):
        result = subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/f'command-{index}.log').write_bytes(result.stdout)
        if result.returncode:
            raise RuntimeError('Diagnostic packaging failed')
    pbo = addons/(prefix+'.pbo')
    _, properties, entries = read_pbo(pbo)
    assert properties['prefix'] == prefix
    assert entries == {p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    (mod/'Addons').mkdir(parents=True)
    shutil.copy2(pbo,mod/'Addons'/pbo.name)
    shutil.copytree(mission,destination)
    assert sha(mod/'Addons'/pbo.name) == sha(pbo)
    assert sha(destination/'init.c') == sha(mission/'init.c')
    ref.update(status='PREPARED_DEPLOYED_ENGINE_PENDING',parent_reference_sha256=sha(parent),
               parent_probe_sha256=sha(source),probe_pbo_sha256=sha(pbo),script_sha256=sha(script),
               world_pbo_sha256='d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577',
               capture_api='P:/scripts/1_core/proto/proto.c:134-141 MakeScreenshot; native engine capture, not OS/UI automation',
               metrics_api='P:/scripts/3_game/global/game.c:868-906; proto/proto.c:145-147',
               api_sha256={str(p):sha(p) for p in [Path('P:/scripts/1_core/proto/proto.c'),Path('P:/scripts/3_game/global/game.c')]},
               capture_at_phase_s=25,metrics_window_phase_s=[10,40],
               metrics_limit='Native client counters recorded descriptively; confirm runtime behavior, no dedicated-server FPS inference.',
               deployed_mod=str(mod),deployed_mission=str(destination))
    ref['limits'].append('Engine DDS captures require file/header/pixel checks and visual inspection; request marker alone is not capture evidence.')
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps({k:v for k,v in ref.items() if k not in ('poses','api_sha256')},indent=2))


if __name__ == '__main__':
    main()
