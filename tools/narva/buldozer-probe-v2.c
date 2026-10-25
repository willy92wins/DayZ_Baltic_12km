// Temporary F10 observer: reads native surfaces, no object/world mutations.
// Native definitions: game.c:730,731,929,1162,1163; object.c:293,311,509,869.
// Coordinates are engine local metres, without the TB easting offset 200000.
static void BuldozerMain()
{
    FileHandle report = OpenFile("$profile:narva_probe_v2.log", FileMode.WRITE);
    if (!report) return;
    array<Object> objects = new array<Object>;
    array<CargoBase> cargos = new array<CargoBase>;
    Object item;
    int i, j;
    float d, px, pz;
    FPrintln(report, "NARVA_OBSERVER_V2");
    FPrintln(report, "camera=" + GetGame().GetCurrentCameraPosition());
    FPrintln(report, "camera_direction=" + GetGame().GetCurrentCameraDirection());
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
    CloseFile(report);
}
