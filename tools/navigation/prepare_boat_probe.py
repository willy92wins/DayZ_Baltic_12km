"""Generate a bounded server boat-control calibration plus terrain observation."""
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import shape
from waterway_common import ROOT, sha
from verify_narva_navigation import intersecting_triangles

candidate=ROOT/'tests/narva_navigation_v3'
design=json.loads((candidate/'design.json').read_text())
line=shape(design['river_axis_tb'])
destination=ROOT/'missions/BalticBoat.BalticTrial'
if destination.exists():
    raise ValueError('Fresh boat mission required')
shutil.copytree(ROOT/'missions/BalticBasic.BalticTrial',destination,
                ignore=shutil.ignore_patterns('storage*','*.log','*.RPT'))
route=[line.interpolate(s) for s in range(55,176,10)]
points_code='\n'.join(f'        m_Route.Insert("{p.x-200000:.6f} 0 {p.y:.6f}");' for p in route)
vertices=sorted({ij for tri in intersecting_triangles(shape(design['depth_check_polygon_tb'])) for ij in tri})
samples_code='\n'.join(f'        ObserveGround({6*c}, {12282-6*r});' for r,c in vertices)
source=r'''// Bounded server-owned empty-boat calibration. Never SetPosition after spawn.
// Native Boat API: scripts/3_game/vehicles/boat.c:49,55,97,119,123,139.
// This fixture cannot prove a seated player's clearance or a return journey.
void main()
{
    Hive ce = CreateHive();
    if (ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026, 9, 30, 12, 0);
}

class BalticBoatMission: MissionServer
{
    protected BoatScript m_Boat;
    protected ref array<vector> m_Route;
    protected FileHandle m_Log;
    protected int m_Start;
    protected int m_Tick;
    protected int m_Target;
    protected float m_HealthStart;
    protected bool m_Stopped;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_Route = new array<vector>;
__ROUTE__
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BeginBoatTrial, 40000, false);
    }

    void ObserveGround(float x, float z)
    {
        FPrintln(m_Log, "G;" + x + ";" + z + ";" + GetGame().SurfaceY(x,z) + ";" + GetGame().SurfaceRoadY(x,z) + ";" + GetGame().SurfaceIsSea(x,z));
    }

    void BeginBoatTrial()
    {
        m_Log = OpenFile("$profile:baltic_boat_probe_v3.log", FileMode.WRITE);
        if (!m_Log) return;
        FPrintln(m_Log, "BALTIC_BOAT_PROBE_V3");
        FPrintln(m_Log, "ASC=__ASC__");
        FPrintln(m_Log, "BOOTSTRAP_NAV_STALE_NO_AI_ACCEPTANCE");
        FPrintln(m_Log, "W;" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax() + ";" + GetGame().SurfaceGetSeaLevel());
__SAMPLES__
        array<Object> objects = new array<Object>;
        array<CargoBase> cargos = new array<CargoBase>;
        GetGame().GetObjectsAtPosition3D("2417.143 9 6889.885", 100, objects, cargos);
        for (int index = 0; index < objects.Count(); index++)
        {
            Object obj = objects.Get(index);
            if (!obj) continue;
            string model = obj.GetShapeName();
            if (!model.Contains("bridge_metal_25")) continue;
            vector deck = obj.ModelToWorld("0 8.054884 0");
            FPrintln(m_Log, "O;" + model + ";" + obj.GetPosition() + ";" + obj.GetOrientation() + ";" + deck);
        }
        vector spawn = m_Route.Get(0);
        spawn[1] = GetGame().SurfaceGetSeaLevel() + 0.3;
        m_Boat = BoatScript.Cast(GetGame().CreateObjectEx("Boat_01_Orange", spawn, ECE_CREATEPHYSICS));
        if (!m_Boat)
        {
            Finish("SPAWN_FAILED");
            return;
        }
        vector ahead = m_Route.Get(1) - m_Route.Get(0);
        vector orientation = ahead.VectorToAngles();
        orientation[1] = 0;
        orientation[2] = 0;
        m_Boat.SetOrientation(orientation);
        m_Boat.GetInventory().CreateAttachment("SparkPlug");
        m_Boat.Fill(BoatFluid.FUEL, m_Boat.GetFluidCapacity(BoatFluid.FUEL));
        m_HealthStart = m_Boat.GetHealth("", "Health");
        m_Start = GetGame().GetTime();
        m_Target = 1;
        FPrintln(m_Log, "SPAWN;" + m_Boat.GetPosition() + ";" + m_Boat.GetOrientation() + ";" + m_HealthStart);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BoatTick, 100, true);
    }

    void BoatTick()
    {
        if (m_Stopped) return;
        if (!m_Boat)
        {
            Finish("BOAT_LOST");
            return;
        }
        float seconds = (GetGame().GetTime() - m_Start) * 0.001;
        vector pos = m_Boat.GetPosition();
        vector orientation = m_Boat.GetOrientation();
        vector velocity = GetVelocity(m_Boat);
        float speed = velocity.Length();
        float health = m_Boat.GetHealth("", "Health");
        vector target = m_Route.Get(m_Target);
        vector delta = target - pos;
        delta[1] = 0;
        float targetDistance = delta.Length();
        float steer;
        float throttle;
        if (seconds >= 10 && seconds < 10.3)
        {
            m_Boat.EngineStart();
            m_Boat.ShiftTo(m_Boat.GetNeutralGear() + 1);
        }
        if (seconds >= 11 && m_Boat.EngineIsOn())
        {
            if (targetDistance < 5)
            {
                int finalIndex = m_Route.Count();
                finalIndex -= 1;
                if (m_Target >= finalIndex)
                {
                    Finish("OUTWARD_ROUTE_REACHED_EMPTY_BOAT_ONLY");
                    return;
                }
                m_Target++;
                target = m_Route.Get(m_Target);
                delta = target - pos;
                delta[1] = 0;
            }
            vector heading = delta.VectorToAngles();
            float error = heading[0] - orientation[0];
            while (error > 180) error -= 360;
            while (error < -180) error += 360;
            steer = Math.Clamp(error/40, -0.6, 0.6);
            throttle = 0.22;
            if (speed > 2.5) throttle = 0;
            m_Boat.SetSteering(steer);
            m_Boat.SetThrottle(throttle);
        }
        m_Tick++;
        if (m_Tick % 5 == 0)
        {
            vector propeller = m_Boat.ModelToWorld(m_Boat.PropellerGetPosition());
            string record = "B;" + seconds + ";" + pos[0] + ";" + pos[1] + ";" + pos[2] + ";" + orientation[0] + ";" + speed + ";" + health;
            record = record + ";" + m_Boat.GetFluidFraction(BoatFluid.FUEL) + ";" + m_Boat.EngineIsOn() + ";" + m_Boat.GetCurrentGear();
            record = record + ";" + propeller[1] + ";" + GetGame().GetWaterDepth(propeller) + ";" + m_Boat.GetSteering() + ";" + m_Boat.GetThrottle() + ";" + m_Target;
            FPrintln(m_Log, record);
        }
        if (health < m_HealthStart - 1) Finish("DAMAGE_STOP");
        else if (seconds > 20 && !m_Boat.EngineIsOn()) Finish("ENGINE_STOPPED");
        else if (targetDistance > 40) Finish("OFF_ROUTE_STOP");
        else if (seconds > 180) Finish("TIMEOUT_CONTROL_INCONCLUSIVE");
    }

    void Finish(string reason)
    {
        m_Stopped = true;
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BoatTick);
        if (m_Boat)
        {
            m_Boat.SetThrottle(0);
            m_Boat.SetSteering(0);
            m_Boat.EngineStop();
        }
        if (m_Log)
        {
            FPrintln(m_Log, "END;" + reason);
            CloseFile(m_Log);
            m_Log = null;
        }
    }

    void ~BalticBoatMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BeginBoatTrial);
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BoatTick);
        if (m_Log) CloseFile(m_Log);
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "2357.84 9.2 6899.01";
        pos[1] = GetGame().SurfaceY(pos[0],pos[2]) + 0.2;
        return super.CreateCharacter(identity,pos,ctx,characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticBoatMission();
}
'''
source=source.replace('__ROUTE__',points_code).replace('__SAMPLES__',samples_code).replace('__ASC__',design['candidate_sha256'])
(destination/'init.c').write_text(source,encoding='utf-8')
report={'mission':str(destination),'init_sha256':sha(destination/'init.c'),
        'route_game_xz':[[p.x-200000,p.y] for p in route], 'terrain_vertex_count':len(vertices),
        'max_seconds':180,'motion':'Boat.SetThrottle/SetSteering; no per-tick pose/velocity writes',
        'limits':['Empty boat only; no crew clearance or return journey acceptance.',
                  'Steering sign/physics authority are fixture assumptions to measure, not terrain facts.']}
(ROOT/'evidence/navigation/boat-fixture.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
