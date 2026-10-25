class CfgPatches
{
 class BalticShadowProbeV4
 {
  units[]={};
  weapons[]={};
  requiredVersion=0.1;
  requiredAddons[]={"DZ_Data","BalticTrialWorld"};
 };
};
class CfgMods
{
 class BalticShadowProbeV4
 {
  type="mod";
  dependencies[]={"Mission"};
  class defs
  {
   class missionScriptModule
   {
    value="";
    files[]={"baltic_shadow_probe_v4/scripts/5_Mission"};
   };
  };
 };
};
