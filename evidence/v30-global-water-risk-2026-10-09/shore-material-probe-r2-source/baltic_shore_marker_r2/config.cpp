class CfgPatches { class BalticShoreMarkerR2 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMaterials
{
 class Shore;
 class ShoreWet;
 class BalticShoreMagentaR2: Shore
 {
  ambient[]={1,0,1,0.4}; diffuse[]={1,0,1,1}; forcedDiffuse[]={1,0,1,0}; emmisive[]={1,0,1,0}; specular[]={0,0,0,0};
 };
 class BalticShoreWetGreenR2: ShoreWet
 {
  ambient[]={0,1,0,0.4}; diffuse[]={0,1,0,1}; forcedDiffuse[]={0,1,0,0}; emmisive[]={0,1,0,0}; specular[]={0,0,0,0};
 };
};
class CfgWorlds { class CAWorld; class BalticTrial: CAWorld { shoreMaterial="#BalticShoreMagentaR2"; shoreWetMaterial="#BalticShoreWetGreenR2"; }; };
