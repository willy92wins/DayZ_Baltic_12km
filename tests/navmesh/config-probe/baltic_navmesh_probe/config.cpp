class CfgPatches
{
    class baltic_navmesh_probe
    {
        units[] = {};
        weapons[] = {};
        requiredVersion = 0.1;
        requiredAddons[] = {"DZ_Scripts", "BalticTrialWorld"};
    };
};
class CfgMods
{
    class baltic_navmesh_probe
    {
        dir = "baltic_navmesh_probe";
        name = "Baltic temporary navmesh config probe";
        type = "mod";
        hideName = 1;
        hidePicture = 1;
        dependencies[] = {"Game"};
        class defs
        {
            class gameScriptModule
            {
                value = "";
                files[] = {"baltic_navmesh_probe/scripts/3_Game"};
            };
        };
    };
};
