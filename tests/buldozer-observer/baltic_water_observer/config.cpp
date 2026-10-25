class CfgPatches
{
    class baltic_water_observer
    {
        units[] = {};
        weapons[] = {};
        requiredVersion = 0.1;
        requiredAddons[] = {"DZ_Scripts"};
    };
};
class CfgMods
{
    class baltic_water_observer
    {
        dir = "baltic_water_observer";
        name = "Baltic temporary water observer";
        type = "mod";
        hideName = 1;
        hidePicture = 1;
        dependencies[] = {"Mission"};
        class defs
        {
            class missionScriptModule
            {
                value = "";
                files[] = {"baltic_water_observer/scripts/5_Mission"};
            };
        };
    };
};
