modded class MissionGameplay
{
 protected bool m_BalticOceanStarted;
 protected int m_BalticOceanSample;
 protected float m_BalticOceanNext;
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial" || m_BalticOceanSample>=90) return;
  if (!m_BalticOceanStarted)
  {
   FileHandle first=OpenFile("$profile:baltic_ocean_height_probe_v1.log",FileMode.WRITE);
   if (!first) return;
   FPrintln(first,"BALTIC_OCEAN_HEIGHT_PROBE_V1");
   FPrintln(first,"CFG;"+GetGame().ConfigGetFloat("CfgWorlds BalticTrial MaxTide")+";"+GetGame().ConfigGetFloat("CfgWorlds BalticTrial MaxWave"));
   CloseFile(first);m_BalticOceanStarted=true;
  }
  m_BalticOceanNext-=timeslice;
  if (m_BalticOceanNext>0) return;
  m_BalticOceanNext=1;
  FileHandle file=OpenFile("$profile:baltic_ocean_height_probe_v1.log",FileMode.APPEND);
  if (!file) return;
  FPrintln(file,"SEA;"+m_BalticOceanSample+";"+GetGame().GetTime()+";"+GetGame().SurfaceGetSeaLevel()+";"+GetGame().SurfaceGetSeaWaveCurrent()+";"+GetGame().SurfaceGetSeaWaveMax());
  m_BalticOceanSample++;
  if (m_BalticOceanSample==90) FPrintln(file,"END;90");
  CloseFile(file);
 }
};
