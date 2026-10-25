# V4: repair the measured Mission compile failure

V3 run c5b73597 failed to compile at BalticShadowProbeV3.c:118, Formula too complex. Server remained alive in the compile-error dialog; orderly client close completed and the blocked server required the lifecycle stop. No IDs were loaded and no render option was changed.

V4 changes only the isolated diagnostic namespace/profile-file prefix and expands every long log concatenation into sequential string-leading assignments. It preserves the same message terms/order, A/B/A state machine, SHA-pinned registry IDs, read-only Terrain shadows control and 60-second restoration deadman. No terrain/material/configuration of the map changes.

The native Get/SetEngineValue declarations and the prior registry scanner remain the same as V3's reviewed plan. E32/E33 in dayz-mod-implementation-checklists.md:238-239 establish the compile mechanism and string-leading fix. Client writes remain in MissionGameplay only; server merely compiles the shared Mission script module. There is no RPC or gameplay state.

Validate one actual script with the structural linter, CfgConvert config, exact PBO source bytes and deployed hash. A fresh DayZ compile/ready is required; offline lint is not compiler proof. Then use the original single shadow contrast and restore, only if scene and baseline are usable. No manual diagnostic IDs.
