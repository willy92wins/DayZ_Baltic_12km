"""Isolated elevated vanilla pond consumer; derive only from the frozen boat probe."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from attach_navmesh import read_pbo


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    source = ROOT / 'missions/BalticBoatInput.BalticTrial/init.c'
    target = ROOT / 'missions/BalticElevatedWaterV1.BalticTrial'
    if target.exists():
        raise ValueError('Fresh mission required')
    raw = source.read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    text = text.replace('baltic_boat_input_v2.log', 'baltic_elevated_water_v1.log')
    text = text.replace('BALTIC_BOAT_INPUT_V2', 'BALTIC_ELEVATED_WATER_V1')
    text = text.replace('CallLater(BeginCalibration, 45000, false)',
                        'CallLater(PrepareWater, 15000, false)')
    start = text.index('        bool waterValid = true;')
    end = text.index('        m_Boat = BoatScript.Cast', start)
    text = text[:start] + '''        LogWater("AFTER");
        vector check = "500 20 3000";
        float waterY = GetGame().GetWaterSurfaceHeightNoFakeWave(check);
        float levelError = waterY - 6;
        levelError = Math.AbsFloat(levelError);
        bool isPond = GetGame().SurfaceIsPond(500,3000);
        if (!isPond || levelError > 0.1)
        {
            Finish("ELEVATED_WATER_NOT_REGISTERED");
            return;
        }
        m_Origin = "500 6.3 3000";
''' + text[end:]
    text = text.replace('        m_Log = OpenFile("$profile:baltic_elevated_water_v1.log", FileMode.WRITE);\n        if (!m_Log) return;\n        FPrintln(m_Log, "BALTIC_ELEVATED_WATER_V1");\n', '')
    marker = '    void BeginCalibration()'
    assert text.count(marker) == 1
    text = text.replace(marker, '''    void LogWater(string stage)
    {
        for (int xx = 400; xx <= 600; xx += 25)
        {
            for (int zz = 2900; zz <= 3200; zz += 25)
            {
                float ground = GetGame().SurfaceY(xx,zz);
                for (int yy = 0; yy <= 9; yy += 3)
                {
                    vector pos = Vector(xx,yy,zz);
                    vector above = Vector(xx,20,zz);
                    string row = "WATER;" + stage + ";" + xx + ";" + yy + ";" + zz + ";" + ground;
                    row = row + ";" + GetGame().SurfaceIsSea(xx,zz) + ";" + GetGame().SurfaceIsPond(xx,zz);
                    row = row + ";" + GetGame().GetWaterDepth(pos) + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(above);
                    FPrintln(m_Log,row);
                }
            }
        }
    }

    void PrepareWater()
    {
        m_Log = OpenFile("$profile:baltic_elevated_water_v1.log", FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log,"BALTIC_ELEVATED_WATER_V1");
        LogWater("BEFORE");
        for (int xx = 450; xx <= 550; xx += 50)
        {
            for (int zz = 2950; zz <= 3150; zz += 50)
            {
                vector pos = Vector(xx,6,zz);
                Object pond = GetGame().CreateObjectEx("StaticObj_water_pond_50x50m",pos,ECE_NONE);
                if (!pond)
                {
                    Finish("POND_CREATE_FAILED");
                    return;
                }
                pond.SetPosition(pos);
                FPrintln(m_Log,"POND;" + pond.GetType() + ";" + pond.GetPosition());
            }
        }
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginCalibration,3000,false);
    }

''' + marker)
    text = text.replace('else if (GetGame().SurfaceY(pos[0],pos[2]) > -3)',
                        'else if (GetGame().SurfaceY(pos[0],pos[2]) > 2.5)')
    text = text.replace('        else if (seconds >= 85)',
                        '        else if (seconds > 3 && (pos[1] < 4 || pos[1] > 8)) Finish("BUOYANCY_FAILED");\n        else if (seconds >= 85)')
    text = text.replace('pos = "2020 0 11200";', 'pos = "610 0 3000";')
    text = text.replace('pos[1] = GetGame().SurfaceGetSeaLevel() + 0.3;', 'pos[1] = GetGame().SurfaceY(pos[0],pos[2]) + 0.3;')
    text = text.replace('GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BeginCalibration);',
                        'GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(PrepareWater);\n        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BeginCalibration);')
    # Reuse the deployed consumer only if its script is byte-identical to source.
    pbo = Path('P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo')
    pbo_raw, props, entries = read_pbo(pbo)
    script = ROOT / 'diagnostics/baltic_boat_input/scripts/4_World/BalticBoatInput.c'
    matching = [v for k,v in entries.items() if k.lower().endswith('balticboatinput.c')]
    if matching != [script.read_bytes()] or props.get('prefix') != 'baltic_boat_input':
        raise ValueError('Deployed input addon differs from inspected source')
    target.mkdir()
    (target/'init.c').write_text(text, encoding='utf-8', newline='\n')
    receipt = {'status':'PREPARED_NOT_EXECUTED', 'source_sha256':digest(raw),
               'mission_sha256':digest((target/'init.c').read_bytes()),
               'input_addon_sha256':digest(pbo_raw), 'site_xz':[500,3000],
               'water_target_y':6, 'tile_centres_x':[450,500,550],
               'tile_centres_z':[2950,3000,3050,3100,3150],
               'tile_extent_m':52, 'scope':'Dynamic objects first; no terrain edit or WRP acceptance.'}
    out = ROOT/'evidence/regional-foundation-v1/elevated-water-preparation.json'
    out.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__':
    main()
