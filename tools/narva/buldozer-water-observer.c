// Read-only Buldozer F10 observer. Local output only; no world mutations.
// game.c:1162,1174-1187; ensystem.c:417,443,481. No server/RPC state.
static void BuldozerMain()
{
    FileHandle report = OpenFile("$profile:baltic_water_observer_v1.log", FileMode.WRITE);
    if (!report) return;
    int i, j;
    float px, pz, terrain;
    vector pos;
    string line;
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
}
