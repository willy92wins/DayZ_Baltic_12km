// Local navigation generation only. No economy, population or player setup.
// Consumer pattern: official DayZ:Generating_navigation_mesh and
// P:/scripts/5_Mission/somemission.c:7-9 (MissionServer).
void main()
{
    Print("BALTIC_NAVMESH_MISSION_MAIN_V1");
}

Mission CreateCustomMission(string path)
{
    return new MissionServer();
}
