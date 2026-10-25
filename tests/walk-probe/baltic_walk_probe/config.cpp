class CfgPatches
{
    class baltic_walk_probe
    {
        units[] = {};
        weapons[] = {};
        requiredVersion = 0.1;
        requiredAddons[] = {"DZ_Scripts", "BalticTrialWorld"};
    };
};
class CfgMods
{
    class baltic_walk_probe
    {
        dir = "baltic_walk_probe";
        name = "Baltic temporary bounded walking probe";
        type = "mod";
        hideName = 1;
        hidePicture = 1;
        dependencies[] = {"Mission"};
        class defs
        {
            class missionScriptModule
            {
                value = "";
                files[] = {"baltic_walk_probe/scripts/5_Mission"};
            };
        };
    };
};
