void main() { GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0); }
class BalticKit7NavDataMission: MissionServer {}
Mission CreateCustomMission(string path) { return new BalticKit7NavDataMission(); }
