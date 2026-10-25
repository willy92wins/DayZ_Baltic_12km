// EV32: one transient client option. No Apply or persistent settings writes.
modded class MissionGameplay
{
 protected ref GameOptions m_BalticDetailOptions;
 protected ListOptionsAccess m_BalticDetailOption;
 protected bool m_BalticDetailStarted;
 protected bool m_BalticDetailRefused;
 protected int m_BalticDetailOriginal;
 protected int m_BalticDetailPhase;
 protected int m_BalticDetailNext;
 protected int m_BalticDetailDeadline;

 void BalticDetailLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_detail_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }
 void BalticDetailRestore(int now, string reason)
 {
  m_BalticDetailOption.Revert();
  m_BalticDetailPhase = 2;
  BalticDetailLog("PHASE;2;" + now + ";" + reason + ";index=" + m_BalticDetailOption.GetIndex() + ";changed=" + m_BalticDetailOption.IsChanged());
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer() || m_BalticDetailRefused) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  int now = GetGame().GetTime();
  if (now < m_BalticDetailNext) return;
  m_BalticDetailNext = now + 1000;
  if (!m_BalticDetailStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_detail_probe_v1.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_DETAIL_PROBE_V1;EV32");
   CloseFile(first);
   m_BalticDetailOptions = new GameOptions();
   m_BalticDetailOption = ListOptionsAccess.Cast(m_BalticDetailOptions.GetOptionByType(OptionAccessType.AT_OPTIONS_TERRAIN));
   if (!m_BalticDetailOption)
   {
    BalticDetailLog("REFUSED;missing_option");
    m_BalticDetailRefused = true;
    return;
   }
   m_BalticDetailOriginal = m_BalticDetailOption.GetIndex();
   BalticDetailLog("ORIGINAL;" + m_BalticDetailOriginal + ";count=" + m_BalticDetailOption.GetItemsCount() + ";restart=" + m_BalticDetailOption.NeedRestart() + ";changed=" + m_BalticDetailOption.IsChanged());
   for (int i = 0; i < m_BalticDetailOption.GetItemsCount(); i++)
   {
    string label;
    m_BalticDetailOption.GetItemText(i, label);
    BalticDetailLog("OPTION;" + i + ";" + label);
   }
   if (m_BalticDetailOption.IsChanged() || m_BalticDetailOption.NeedRestart())
   {
    BalticDetailLog("REFUSED;initial_change_or_restart");
    m_BalticDetailRefused = true;
    return;
   }
   m_BalticDetailStarted = true;
   BalticDetailLog("PHASE;0;" + now);
  }
  if (m_BalticDetailPhase == 1 && now >= m_BalticDetailDeadline) BalticDetailRestore(now, "watchdog");
  FileHandle command = OpenFile("$profile:baltic_detail_probe_v1.phase", FileMode.READ);
  if (command)
  {
   string marker;
   string requested;
   string indexText;
   FGets(command, marker);
   FGets(command, requested);
   FGets(command, indexText);
   CloseFile(command);
   marker = marker.Trim();
   requested = requested.Trim();
   indexText = indexText.Trim();
   if (marker == "EV32-20261009")
   {
    int index = indexText.ToInt();
    if (requested == "1" && m_BalticDetailPhase == 0 && index >= 0 && index < m_BalticDetailOption.GetItemsCount() && index != m_BalticDetailOriginal && index.ToString() == indexText)
    {
     m_BalticDetailOption.SetIndex(index);
     m_BalticDetailOption.Test();
     m_BalticDetailPhase = 1;
     m_BalticDetailDeadline = now + 90000;
     BalticDetailLog("PHASE;1;" + now + ";index=" + m_BalticDetailOption.GetIndex() + ";changed=" + m_BalticDetailOption.IsChanged() + ";restart=" + m_BalticDetailOption.NeedRestart());
     if (m_BalticDetailOption.NeedRestart()) BalticDetailRestore(now, "restart_required");
    }
    if (requested == "2" && m_BalticDetailPhase == 1) BalticDetailRestore(now, "requested");
   }
  }
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  BalticDetailLog("SAMPLE;" + m_BalticDetailPhase + ";" + now + ";index=" + m_BalticDetailOption.GetIndex() + ";fps=" + GetGame().GetLastFPS() + ";" + camera.ToString() + ";" + direction.ToString());
 }
};
