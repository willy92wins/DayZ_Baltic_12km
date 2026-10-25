// One-shot read-only diagnostic, before mission/world load. Never ship.
// Sources: scripts/3_Game/global/game.c:448,611; 3_Game/dayzgame.c:994;
// scripts/1_Core/proto/ensystem.c:397. FileExist is observational only.
modded class DayZGame
{
    void DayZGame()
    {
        string balticPath;
        string vanillaPath;
        string worldPath;
        bool balticFound = ConfigGetText("CfgWorlds BalticTrial Navmesh navmeshName", balticPath);
        bool vanillaFound = ConfigGetText("CfgWorlds ChernarusPlus Navmesh navmeshName", vanillaPath);
        bool worldFound = ConfigGetText("CfgWorlds BalticTrial worldName", worldPath);
        bool bootstrapFound = ConfigIsExisting("CfgPatches baltic_navmesh_bootstrap_v1");
        Print("BALTIC_NAV_CONFIG_V1_BEGIN");
        Print("BALTIC_NAV_CONFIG_V1_BALTIC found=" + balticFound + " path=" + balticPath + " file=" + FileExist(balticPath));
        Print("BALTIC_NAV_CONFIG_V1_VANILLA found=" + vanillaFound + " path=" + vanillaPath + " file=" + FileExist(vanillaPath));
        Print("BALTIC_NAV_CONFIG_V1_WORLD found=" + worldFound + " path=" + worldPath + " file=" + FileExist(worldPath));
        Print("BALTIC_NAV_CONFIG_V1_BOOTSTRAP=" + bootstrapFound);
        Print("BALTIC_NAV_CONFIG_V1_END");
    }
};
