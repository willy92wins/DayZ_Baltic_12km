class CfgPatches
{
 class BalticTerrainDetailDiagnostic
 {
  units[]={}; weapons[]={}; requiredVersion=0.1;
  requiredAddons[]={"DZ_Data","BalticTrialWorld"};
 };
};
class CfgMods
{
 class BalticTerrainDetailDiagnostic
 {
  type="mod";
  dependencies[]={"Mission"};
  class defs
  {
   class missionScriptModule
   {
    value="";
    files[]={"baltic_terrain_detail/scripts/5_Mission"};
   };
  };
 };
};
