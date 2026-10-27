// Isolated server baseline: no Hive, CE, population or player creation.
// Contracts: scripts/3_game/global/game.c:878-913,1510;
// scripts/5_mission/mission/missionserver.c:102. No network state.
void main()
{
    Print("BALTIC_TERRAIN_PERF_MAIN_V1");
}

class BalticTerrainPerfMission: MissionServer
{
    protected float m_Start;
    protected float m_WindowStart;
    protected float m_Next;
    protected int m_Sample;
    protected int m_Frames;
    protected float m_SumDt;
    protected float m_MaxDt;
    protected int m_Over50;
    protected bool m_Recording;
    protected bool m_Finished;

    override void OnInit()
    {
        super.OnInit();
        string actualWorld = GetGame().GetWorldName();
        actualWorld.ToLower();
        if (!GetGame().IsDedicatedServer() || actualWorld != "baltictrial")
        {
            m_Finished = true;
            return;
        }
        m_Start = GetGame().GetTickTime();
        FileHandle report = OpenFile("$profile:baltic_ab_04_490f5a543295.log", FileMode.WRITE);
        if (!report)
        {
            m_Finished = true;
            return;
        }
        FPrintln(report, "BALTIC_TERRAIN_PERF_V1;" + GetGame().GetWorldName() + ";SERVER;NO_CE_NO_PLAYERS");
        FPrintln(report, "INIT;" + m_Start + ";" + GetGame().GetTime());
        FPrintln(report, "columns;sample;tick;mission_ms;window_s;updates;sum_timeslice;max_timeslice;over50ms;fps_min64;fps_max64;fps_avg64");
        CloseFile(report);
        Print("BALTIC_TERRAIN_PERF_INIT_V1");
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (m_Finished) return;
        float now = GetGame().GetTickTime();
        if (!m_Recording)
        {
            if (now - m_Start < 30) return;
            m_Recording = true;
            m_WindowStart = now;
            m_Next = now + 1;
            return;
        }
        m_Frames++;
        m_SumDt += timeslice;
        m_MaxDt = Math.Max(m_MaxDt, timeslice);
        if (timeslice > 0.05) m_Over50++;
        if (now < m_Next) return;
        FileHandle report = OpenFile("$profile:baltic_ab_04_490f5a543295.log", FileMode.APPEND);
        if (!report)
        {
            m_Finished = true;
            return;
        }
        m_Sample++;
        string row = "S;" + m_Sample + ";" + now + ";" + GetGame().GetTime();
        row = row + ";" + (now - m_WindowStart) + ";" + m_Frames + ";" + m_SumDt + ";" + m_MaxDt + ";" + m_Over50;
        row = row + ";" + GetGame().GetMinFPS(64) + ";" + GetGame().GetMaxFPS(64) + ";" + GetGame().GetAvgFPS(64);
        FPrintln(report, row);
        if (m_Sample == 120)
        {
            FPrintln(report, "END;120;" + now);
            Print("BALTIC_TERRAIN_PERF_COMPLETE_V1");
            m_Finished = true;
        }
        CloseFile(report);
        m_WindowStart = now;
        m_Next = now + 1;
        m_Frames = 0;
        m_SumDt = 0;
        m_MaxDt = 0;
        m_Over50 = 0;
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticTerrainPerfMission();
}
