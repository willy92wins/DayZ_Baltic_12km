class CfgPatches
{
    class baltic_visual_ui_probe
    {
        units[] = {};
        weapons[] = {};
        requiredVersion = 0.1;
        requiredAddons[] = {"DZ_Scripts", "BalticTrialWorld"};
    };
};
class CfgMods
{
    class baltic_visual_ui_probe
    {
        dir = "baltic_visual_ui_probe";
        name = "Baltic temporary visual UI fixture";
        type = "mod";
        hideName = 1;
        hidePicture = 1;
        dependencies[] = {"Mission"};
        class defs
        {
            class missionScriptModule
            {
                value = "";
                files[] = {"baltic_visual_ui_probe/scripts/5_Mission"};
            };
        };
    };
};
