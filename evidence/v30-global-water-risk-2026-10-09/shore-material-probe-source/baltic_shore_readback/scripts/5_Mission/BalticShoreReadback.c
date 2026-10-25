modded class MissionGameplay
{
 protected bool m_BalticShoreLogged;
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (m_BalticShoreLogged || GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") return;
  FileHandle file=OpenFile("$profile:baltic_shore_readback_v1.log",FileMode.WRITE);
  if (!file) return;
  FPrintln(file,"BALTIC_SHORE_COMPONENT_READBACK_V1");
  array<string> keys={"seaMaterial","shoreMaterial","shoreFoamMaterial","shoreWetMaterial"};
  for (int i=0;i<keys.Count();i++)
  {
   string value;
   bool found=GetGame().ConfigGetText("CfgWorlds BalticTrial "+keys[i],value);
   FPrintln(file,keys[i]+";"+found+";"+value);
  }
  FPrintln(file,"END");CloseFile(file);m_BalticShoreLogged=true;
 }
};
