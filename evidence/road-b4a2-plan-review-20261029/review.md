**Verdict: CONDITIONALLY EXECUTABLE.** The finite discovery is justified as a pre-build step, but Step 4's grammar cannot be fixed "before the code" without one bounded probe, and the Step 6 acceptance can false-pass as written.

**Is finite discovery justified before build?** Yes. B4A1 shows byte differences with no cause, and the roads PBO has at least one external reference. A bounded manifest with per-edge provenance is the cheapest way to turn "bytes differ" into either a resolved set or named gaps. The plan correctly refuses to let eight pins stand for the 5509-model scene. Keep that refusal verbatim in the output contract.

**Needs prior discovery (two probes, both inside the existing 120s/512MiB budget):**

- **RVMAT encoding is unknown.** The only pinned CfgConvert evidence is config.bin decoding at road_consumer_discovery_ev112.py:86. Decoding RVMAT is H2, untested. Read the first 4 bytes of both installed RVMAT. Text means parse directly. The raP magic means one CfgConvert run per file, output captured as a sample. The concrete grammar and fixtures must be written against that sample, not before it. The plan's sequence "grammar before code" is right, but "grammar before sample" is not possible without inventing format.
- **Prefix property presence in surfaces/surfaces_bliss.** If the property is absent, the resolution rule has nothing to match. Define now: missing prefix means UNRESOLVED_EXTERNAL for that PBO, never basename fallback.

**False-pass risks and minimal fixes:**

1. **Consumer shares the parser's blind spot.** Step 6 verifies "referencias tokenizadas". If those tokens come from the Step 4 parser, a reference the parser never produced yields no edge, and the consumer passes. Fix: the consumer must do an independent raw scan of the saved originals for any string literal containing a path separator, the .paa or .rvmat suffix, or the `#(` prefix. Each hit must map to an edge or an explicit INCONCLUSIVE token. Any unmapped hit blocks closure.
2. **"Materiales comprendidos íntegramente" is not measurable.** Define it as byte coverage: every byte of the material text is assigned to a token class, with zero unknown tokens and zero skipped spans. Report coverage as a number in the manifest. Anything under full coverage forces INCONCLUSIVE_DEPENDENCIES.
3. **Model roots depend on R0's catalogue.** Models are not decoded here, so the material and texture roots come entirely from R0. The contract must pin the R0 entries.json path and SHA and record that its reference list covers all LODs. Otherwise the "non-visual LOD" fixture tests a case the real run cannot detect.
4. **"Nodo anidado omitido" fixture must mutate the parser, not the manifest.** A co-mutated negative is only meaningful if the consumer catches a parser that silently drops a nested class. State this in the fixture spec.

**Parser scope, stated plainly.** Promise only: class and nested class with braces, `name = "string";`, `name[] = {...};`, `//` and `/* */` comments, doubled-quote escapes. Everything else is an unknown token. Includes, macros, `__EVAL`, and unterminated constructs are INCONCLUSIVE by construction. This is a grammar limit, not a claim about what the engine accepts. Do not phrase the output as "all references found", only "all references within grammar G found, coverage N".

**Source and budget.** The draft names R0 and B4A1 artifacts but gives no SHA for the R0 report or B4A1 approval. Add those pins in Step 1 or the contract is not exact. Budget is adequate: the two surfaces PBOs are read header-only by streaming, and two 30s conversions fit the 120s cap with margin. Keep "no internal retries".

**One-line output rule.** DEPENDENCY_SET_CLOSED_CONDITIONAL requires full byte coverage, zero unmapped raw hits, every edge with provider+path+hash, and no AMBIGUOUS_PROVIDER. Anything else is INCONCLUSIVE_DEPENDENCIES with the pending node list. The old SOURCE_UNSTABLE states remain unexplained either way, and this unit should say so.