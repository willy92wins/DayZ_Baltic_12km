// Read-only bounded discriminator: same deployed WRP/NM, alternative filters/heights.
// Contracts: scripts/3_game/ai/aiworld.c:80,111,137; global/game.c:448,523,1162-1164.
void main() { Print("BALTIC_NAV_SEAM_MAIN_V1"); }

static void BalticSeamSample(FileHandle report, string label, vector requested, PGFilter filter)
{
    vector sampled;
    bool found = GetGame().GetWorld().GetAIWorld().SampleNavmeshPosition(requested, 2, filter, sampled);
    FPrintln(report, "S;" + label + ";" + requested + ";" + found + ";" + sampled);
}

static void BalticNavSeam()
{
    if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
    FileHandle report = OpenFile("$profile:baltic_nav_seam_v1.log", FileMode.WRITE);
    if (!report) return;
    FPrintln(report, "BALTIC_NAV_SEAM_V1");
    string worldPath, navPath, isolated;
    GetGame().ConfigGetText("CfgWorlds BalticTrial worldName", worldPath);
    GetGame().ConfigGetText("CfgWorlds BalticTrial Navmesh navmeshName", navPath);
    GetGame().ConfigGetText("CfgWorlds BalticTrial Navmesh filterIsolatedIslandsOnLoad", isolated);
    FPrintln(report, "CONFIG;" + worldPath + ";" + navPath + ";" + isolated);
    PGFilter walk = new PGFilter;
    walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
    PGFilter all = new PGFilter;
    all.SetFlags(PGPolyFlags.ALL, PGPolyFlags.NONE, PGPolyFlags.NONE);
    vector position;
    float x, z, surface, road;
    int i, j;
    for (i = 0; i <= 16; i++)
    {
        x = 2420 + i * 5;
        for (j = 0; j <= 4; j++)
        {
            z = 6860 + j * 12;
            surface = GetGame().SurfaceY(x, z);
            road = GetGame().SurfaceRoadY(x, z);
            FPrintln(report, "G;" + x + ";" + z + ";" + surface + ";" + road);
            position = Vector(x, road, z);
            BalticSeamSample(report, "walk_road", position, walk);
            BalticSeamSample(report, "all_road", position, all);
            position[1] = 2;
            BalticSeamSample(report, "all_low", position, all);
            position[1] = 9;
            BalticSeamSample(report, "all_high", position, all);
        }
    }
    FPrintln(report, "BALTIC_NAV_SEAM_COMPLETE");
    CloseFile(report);
    Print("BALTIC_NAV_SEAM_COMPLETE_V1");
}

class BalticNavSeamMission: MissionServer
{
    override void OnInit()
    {
        super.OnInit();
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BalticNavSeam, 15000, false);
    }
    void ~BalticNavSeamMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BalticNavSeam);
    }
}
Mission CreateCustomMission(string path) { return new BalticNavSeamMission(); }
