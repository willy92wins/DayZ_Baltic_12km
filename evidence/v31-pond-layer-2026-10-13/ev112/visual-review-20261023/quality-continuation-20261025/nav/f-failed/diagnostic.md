# F nav generation interrupted — 2026-10-25

Run4944fd64, PID174160, start21:14:00.672534UTC. Generator reached63% and reported Data Server Disconnected. Server RPT ends with Destroying game at22:14:05UTC and Termination successfully completed at22:14:06UTC. No usable NM was created; generation.json records GENERATION_FAILED after terminating only the disconnected own generator235028. Inputs remained byte-identical.

The redacted coordinator audit records a successful heartbeat22:13:29UTC, then run_reaped22:14:11UTC. The lease expiration is later,22:17:04UTC. Therefore lease expiry is not established as the cause of the earlier server exit. No lifecycle close or idle-timeout entry for this run appears in the inspected current audit. The bounded source search found no configured one-hour run limit in lifecycle/MCP mission code. The approximately60-minute duration is an observation, not a root cause.

Do not call this an engine crash: the recorded shutdown was orderly and no crash mechanism was isolated. Do not change the map, launcher registration, MCP credentials or permissions to work around an unknown cause. The one-attempt plan remains exhausted; no blind regeneration was started. A further attempt needs a concrete discriminating plan tied to this evidence. Forest measurements were separated onto the unchanged original F in data-server mode, which carries no normal-NM or AI acceptance.

Full RPT and script log remain local. Only hashes, selected diagnostics and redacted audit are eligible for publication; server credentials/config bytes are excluded.
