// Temporary diagnostic only. Test applies without writing the user's profile.
modded class MissionGameplay
{
 protected ref GameOptions m_BalticDetailOptions;
 protected ListOptionsAccess m_BalticDetailOption;
 protected bool m_BalticDetailReady;
 protected int m_BalticDetailOriginal;
 protected int m_BalticDetailNext;
 protected string m_BalticDetailCommand;
 void BalticDetailLog(string row)
 {
  FileHandle f=OpenFile("$profile:baltic_terrain_detail_v1.log",FileMode.APPEND);
  if (!f) return;
  FPrintln(f,row);CloseFile(f);
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") return;
  if (!m_BalticDetailReady)
  {
   m_BalticDetailOptions=new GameOptions();
   m_BalticDetailOptions.Initialize();
   m_BalticDetailOption=ListOptionsAccess.Cast(m_BalticDetailOptions.GetOptionByType(AT_OPTIONS_TERRAIN));
   if (!m_BalticDetailOption) return;
   m_BalticDetailOriginal=m_BalticDetailOption.GetIndex();
   FileHandle first=OpenFile("$profile:baltic_terrain_detail_v1.log",FileMode.WRITE);
   if (!first) return;
   FPrintln(first,"BALTIC_TERRAIN_DETAIL_V1");CloseFile(first);
   BalticDetailLog("ORIGINAL;"+m_BalticDetailOriginal+";"+m_BalticDetailOption.GetItemsCount());
   for (int i=0;i<m_BalticDetailOption.GetItemsCount();i++)
   {
    string label;
    m_BalticDetailOption.GetItemText(i,label);
    BalticDetailLog("ITEM;"+i+";"+label);
   }
   m_BalticDetailReady=true;
  }
  if (GetGame().GetTime()<m_BalticDetailNext) return;
  m_BalticDetailNext=GetGame().GetTime()+1000;
  FileHandle input=OpenFile("$profile:baltic_terrain_detail_v1.command",FileMode.READ);
  if (!input) return;
  string command;
  FGets(input,command);CloseFile(input);
  if (command==m_BalticDetailCommand || command=="") return;
  array<string> fields=new array<string>;
  command.Split(";",fields);
  if (fields.Count()!=2) { BalticDetailLog("REJECT;SCHEMA");return; }
  int index=fields[1].ToInt();
  if (index<0 || index>=m_BalticDetailOption.GetItemsCount()) { BalticDetailLog("REJECT;INDEX");return; }
  vector cam=GetGame().GetCurrentCameraPosition();
  if (vector.Distance(cam,"2185 280 7350")>1) { BalticDetailLog("REJECT;CAMERA");return; }
  m_BalticDetailOption.SetIndex(index);
  m_BalticDetailOption.Test();
  m_BalticDetailCommand=command;
  string record="SET;"+GetGame().GetTime()+";"+fields[0]+";"+index;
  record=record+";"+m_BalticDetailOption.GetIndex()+";"+m_BalticDetailOption.NeedRestart();
  BalticDetailLog(record);
 }
 override void OnMissionFinish()
 {
  if (m_BalticDetailReady && m_BalticDetailOption)
  {
   m_BalticDetailOption.SetIndex(m_BalticDetailOriginal);
   m_BalticDetailOption.Test();
   BalticDetailLog("RESTORED;"+m_BalticDetailOption.GetIndex());
  }
  super.OnMissionFinish();
 }
};
