// Temporary local instrumentation; never compiled into a normal game mission.
// Source contracts and test budget: plans/buldozer-auto-observer.md.
#ifdef BULDOZER
#ifdef DIAG_DEVELOPER
modded class MissionGameplay
{
    protected float m_BalticObserverElapsed;
    protected bool m_BalticObserverWritten;

    void MissionGameplay()
    {
        Print("BALTIC_AUTO_OBSERVER_V1_CONSTRUCTED");
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (m_BalticObserverWritten) return;
        m_BalticObserverElapsed = m_BalticObserverElapsed + timeslice;
        if (m_BalticObserverElapsed < 10.0) return;
        m_BalticObserverWritten = true;
        BalticWriteWaterObservation();
    }

    protected void BalticWriteWaterObservation()
    {
        FileHandle report;
        int i, j;
        float px, pz, terrain;
        vector pos;
        string line;
        string path = "$profile:baltic_water_observer_auto_v1.log";
        if (FileExist(path))
        {
            Print("BALTIC_AUTO_OBSERVER_V1_REFUSED_EXISTING_LOG");
            return;
        }
        report = OpenFile(path, FileMode.WRITE);
        if (!report)
        {
            Print("BALTIC_AUTO_OBSERVER_V1_OPEN_FAILED");
            return;
        }
        FPrintln(report, "BALTIC_WATER_OBSERVER_V1");
        FPrintln(report, "sea_min=" + GetGame().SurfaceGetSeaLevelMin());
        FPrintln(report, "sea_max=" + GetGame().SurfaceGetSeaLevelMax());
        FPrintln(report, "sea_now=" + GetGame().SurfaceGetSeaLevel());
        FPrintln(report, "wave_max=" + GetGame().SurfaceGetSeaWaveMax());
        FPrintln(report, "wave_now=" + GetGame().SurfaceGetSeaWaveCurrent());
        FPrintln(report, "GRID;x;z;terrain;sea;pond;depth_at_terrain;surface_no_fake;surface_with_fake");
        for (i = 0; i <= 20; i++)
        {
            px = 1800 + i * 60;
            for (j = 0; j <= 20; j++)
            {
                pz = 6300 + j * 60;
                terrain = GetGame().SurfaceY(px, pz);
                pos = Vector(px, terrain, pz);
                line = "G;" + px + ";" + pz + ";" + terrain;
                line = line + ";" + GetGame().SurfaceIsSea(px, pz) + ";" + GetGame().SurfaceIsPond(px, pz);
                line = line + ";" + GetGame().GetWaterDepth(pos);
                line = line + ";" + GetGame().GetWaterSurfaceHeightNoFakeWave(pos);
                line = line + ";" + GetGame().GetWaterSurfaceHeightWithFakeWave(pos);
                FPrintln(report, line);
            }
        }
        FPrintln(report, "END_BALTIC_WATER_OBSERVER_V1");
        CloseFile(report);
        Print("BALTIC_AUTO_OBSERVER_V1_COMPLETE_441");
    }
}
#endif
#endif
