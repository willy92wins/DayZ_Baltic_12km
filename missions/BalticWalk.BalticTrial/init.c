// Dedicated local prototype only. No gameplay economy or AI population.
// APIs verified in installed scripts:
// 3_Game/hive/hive.c:11,29; global/world.c:51; global/game.c:933,1162,1525;
// 5_Mission/mission/missionserver.c:83,486,541. Probe APIs have a real V3 consumer trace.
void main()
{
    Hive ce = CreateHive();
    if (ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
    // Temporary deterministic render mission. Weather APIs: scripts/3_game/weather.c.
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 0);
    weather.GetRain().Set(0, 0, 3600);
    weather.GetFog().SetLimits(0, 0);
    weather.GetFog().Set(0, 0, 3600);
    weather.GetSnowfall().SetLimits(0, 0);
    weather.GetSnowfall().Set(0, 0, 3600);
    weather.SetWindSpeed(0);
    weather.SetStorm(0, 1, 3600);
}

static void BalticTrialObserve()
{
    FileHandle report = OpenFile("$profile:baltic_trial_probe_v1.log", FileMode.WRITE);
    if (!report) return;
    array<Object> objects = new array<Object>;
    array<CargoBase> cargos = new array<CargoBase>;
    Object item;
    int i, j;
    float d, px, pz, width;
    FPrintln(report, "BALTIC_TRIAL_OBSERVER_V1");
    FPrintln(report, "world=" + GetGame().GetWorldName());
    GetGame().GetObjectsAtPosition3D("2417.143 0 6889.885", 100, objects, cargos);
    for (i = 0; i < objects.Count(); i++)
    {
        item = objects.Get(i);
        if (!item) continue;
        FPrintln(report, "shape=" + item.GetShapeName());
        FPrintln(report, "position=" + item.GetPosition());
        FPrintln(report, "orientation=" + item.GetOrientation());
        FPrintln(report, "raw_roadway_mid_world=" + item.ModelToWorld("0 8.054884 0"));
        FPrintln(report, "raw_roadway_end_negative_world=" + item.ModelToWorld("0 8.054884 -12.5"));
        FPrintln(report, "raw_roadway_end_positive_world=" + item.ModelToWorld("0 8.054884 12.5"));
    }
    FPrintln(report, "PROFILE;distance;x;z;terrain;road");
    for (i = -144; i <= 144; i++)
    {
        d = i * 0.25;
        px = 2417.143 + 0.988364361 * d;
        pz = 6889.885 - 0.152104866 * d;
        FPrintln(report, "P;" + d + ";" + px + ";" + pz + ";" + GetGame().SurfaceY(px, pz) + ";" + GetGame().SurfaceRoadY(px, pz));
    }
    FPrintln(report, "GRID;x;z;terrain");
    for (i = 0; i <= 16; i++)
    {
        px = 2394 + i * 3;
        for (j = 0; j <= 16; j++)
        {
            pz = 6864 + j * 3;
            FPrintln(report, "G;" + px + ";" + pz + ";" + GetGame().SurfaceY(px, pz));
        }
    }
    FPrintln(report, "sea_level=" + GetGame().SurfaceGetSeaLevel());
    FPrintln(report, "center_is_sea=" + GetGame().SurfaceIsSea(2417.143, 6889.885));
    FPrintln(report, "center_is_pond=" + GetGame().SurfaceIsPond(2417.143, 6889.885));
    FPrintln(report, "center_water_depth=" + GetGame().GetWaterDepth("2417.143 0 6889.885"));
    for (i = -1; i <= 1; i = i + 2)
    {
        d = i * 12.5;
        for (j = -8; j <= 8; j++)
        {
            width = j * 0.5;
            px = 2417.143 + 0.988364361 * d - 0.152104866 * width;
            pz = 6889.885 - 0.152104866 * d - 0.988364361 * width;
            FPrintln(report, "E;" + d + ";" + width + ";" + px + ";" + pz + ";" + GetGame().SurfaceY(px, pz) + ";" + GetGame().SurfaceRoadY(px, pz));
        }
    }
    FPrintln(report, "BALTIC_TRIAL_OBSERVER_COMPLETE");
    CloseFile(report);
}

class BalticTrialMission: MissionServer
{
    override void OnInit()
    {
        super.OnInit();
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BalticTrialObserve, 10000, false);
    }

    void ~BalticTrialMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BalticTrialObserve);
    }

    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        // Fresh characters only. Measured dry west approach, 30 m from bridge center.
        pos = "2387.49 0 6894.45";
        pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticWalkMission();
}

// Separate server-side observation of actual player movement. No position setters.
class BalticWalkMission: BalticTrialMission
{
    protected float m_BalticWalkServerTime;
    protected float m_BalticWalkServerSample;
    protected float m_BalticWalkDriveStart;
    protected float m_BalticWalkDriveTurn;
    protected int m_BalticWalkDrivePhase;
    protected ref array<Man> m_BalticWalkPlayers = new array<Man>;
    override void OnInit()
    {
        super.OnInit();
        FileHandle report = OpenFile("$profile:baltic_walk_server_v1.csv", FileMode.WRITE);
        if (report)
        {
            FPrintln(report, "t;x;y;z;health;swim");
            CloseFile(report);
        }
    }
    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        m_BalticWalkServerTime = m_BalticWalkServerTime + timeslice;
        if (m_BalticWalkServerTime > 240) return;
        m_BalticWalkServerSample = m_BalticWalkServerSample + timeslice;
        if (m_BalticWalkServerSample < 0.25) return;
        m_BalticWalkServerSample = 0;
        m_BalticWalkPlayers.Clear();
        GetGame().GetPlayers(m_BalticWalkPlayers);
        if (m_BalticWalkPlayers.Count() != 1) return;
        PlayerBase player = PlayerBase.Cast(m_BalticWalkPlayers.Get(0));
        if (!player) return;
        vector p = player.GetPosition();
        // Calibration: client-only overrides were reconciled back to the spawn.
        // Apply the same bounded input on the authoritative side; never set position.
        HumanInputController control = player.GetInputController();
        if (control && m_BalticWalkDrivePhase != 4)
        {
            if (m_BalticWalkDriveStart == 0) m_BalticWalkDriveStart = m_BalticWalkServerTime + 10;
            float d = (p[0] - 2417.143) * 0.988364361 - (p[2] - 6889.885) * 0.152104866;
            float cross = (p[0] - 2417.143) * 0.152104866 + (p[2] - 6889.885) * 0.988364361;
            if (m_BalticWalkDrivePhase == 0 && m_BalticWalkServerTime >= m_BalticWalkDriveStart) m_BalticWalkDrivePhase = 1;
            if (m_BalticWalkDrivePhase == 1 && d >= 28)
            {
                m_BalticWalkDrivePhase = 2;
                m_BalticWalkDriveTurn = m_BalticWalkServerTime + 3;
            }
            if (m_BalticWalkDrivePhase == 2 && m_BalticWalkServerTime >= m_BalticWalkDriveTurn) m_BalticWalkDrivePhase = 3;
            if (m_BalticWalkDrivePhase == 3 && d <= -28) m_BalticWalkDrivePhase = 4;
            if (Math.AbsFloat(cross) > 3 || player.GetHealth("", "Health") <= 0 || m_BalticWalkServerTime > m_BalticWalkDriveStart + 120) m_BalticWalkDrivePhase = 4;
            if (m_BalticWalkDrivePhase == 4)
            {
                control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
                control.OverrideMovementAngle(HumanInputControllerOverrideType.DISABLED, 0);
            }
            else
            {
                float speed = 0;
                float angle = 0;
                float targetDistance = 30;
                if (m_BalticWalkDrivePhase == 3) targetDistance = -30;
                if (m_BalticWalkDrivePhase == 1 || m_BalticWalkDrivePhase == 3)
                {
                    speed = 1;
                    float tx = 2417.143 + 0.988364361 * targetDistance - p[0];
                    float tz = 6889.885 - 0.152104866 * targetDistance - p[2];
                    angle = (Math.Atan2(tx, tz) - control.GetHeadingAngle()) * Math.RAD2DEG;
                    while (angle > 180) angle = angle - 360;
                    while (angle < -180) angle = angle + 360;
                }
                control.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED, speed);
                control.OverrideMovementAngle(HumanInputControllerOverrideType.ENABLED, angle);
            }
        }
        int swimming = 0;
        if (player.GetCommand_Swim()) swimming = 1;
        FileHandle report = OpenFile("$profile:baltic_walk_server_v1.csv", FileMode.APPEND);
        if (report)
        {
            FPrintln(report, "" + m_BalticWalkServerTime + ";" + p[0] + ";" + p[1] + ";" + p[2] + ";" + player.GetHealth("", "Health") + ";" + swimming);
            CloseFile(report);
        }
    }
}
