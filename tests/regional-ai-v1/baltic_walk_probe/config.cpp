class CfgPatches
{
    class baltic_walk_probe
    {
        units[]={}; weapons[]={}; requiredVersion=0.1;
        requiredAddons[]={"DZ_Data","DZ_Scripts"};
    };
};
class CfgMods
{
    class baltic_walk_probe
    {
        type="mod";
        dependencies[]={"Mission"};
        class defs
        {
            class missionScriptModule
            {
                value="";
                files[]={"baltic_walk_probe/scripts/5_Mission"};
            };
        };
    };
};
