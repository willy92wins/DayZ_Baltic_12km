class CfgPatches
{
    class baltic_render_probe
    {
        units[] = {};
        weapons[] = {};
        requiredVersion = 0.1;
        requiredAddons[] = {"DZ_Scripts", "BalticTrialWorld"};
    };
};
class CfgMods
{
    class baltic_render_probe
    {
        dir = "baltic_render_probe";
        name = "Baltic temporary deterministic render probe";
        type = "mod";
        hideName = 1;
        hidePicture = 1;
        dependencies[] = {"Mission"};
        class defs
        {
            class missionScriptModule
            {
                value = "";
                files[] = {"baltic_render_probe/scripts/5_Mission"};
            };
        };
    };
};
