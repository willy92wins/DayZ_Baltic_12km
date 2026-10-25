"""Normalize one redundant Codex setting; preserve the daemon authority contract."""
from pathlib import Path
import hashlib, json, re, subprocess, tomllib, traceback
from dayz_mcp import host_config as h

B = Path(__file__).parent
cfg = Path.home() / '.codex/config.toml'
claude = Path.home() / '.claude.json'
binary = Path('C:/Users/guill/AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe')
digest = lambda raw: hashlib.sha256(raw).hexdigest()
raw = cfg.read_bytes()
source = Path(h.__file__)
source_hash = digest(source.read_bytes())
parsed = tomllib.loads(raw.decode('utf-8'))
entry = parsed['mcp_servers']['dayz-mcp']
assert entry.get('enabled') is True
reference = h._registration_from_entry(json.loads(claude.read_bytes())['mcpServers']['dayz-mcp'], platform='claude')
before_error = None
try:
    h._registration_from_entry(entry, platform='codex')
except h.HostConfigError as exc:
    before_error = dict(code=str(exc), frames=[dict(file=Path(f.filename).name, line=f.lineno, function=f.name) for f in traceback.extract_tb(exc.__traceback__)])
assert before_error and before_error['code'] == 'daemon_provenance_conflict'
normalized = {k: v for k, v in entry.items() if k != 'enabled'}
assert h._registration_from_entry(normalized, platform='codex') == reference
before_cli = subprocess.run([str(binary), 'mcp', 'get', 'dayz-mcp', '--json'], capture_output=True, text=True, timeout=20)
assert before_cli.returncode == 0
codex_before = json.loads(before_cli.stdout)
assert codex_before['enabled'] is True

text = raw.decode('utf-8')
header = re.search(r'(?m)^\[mcp_servers\.dayz-mcp\]\r?$', text)
assert header
next_header = re.search(r'(?m)^\[', text[header.end():])
end = header.end() + next_header.start() if next_header else len(text)
block = text[header.start():end]
newblock, count = re.subn(r'(?m)^enabled\s*=\s*true\s*\r?\n', '', block)
assert count == 1
new = (text[:header.start()] + newblock + text[end:]).encode('utf-8')
expected = tomllib.loads(raw.decode('utf-8'))
del expected['mcp_servers']['dayz-mcp']['enabled']
assert tomllib.loads(new.decode('utf-8')) == expected
(B / 'codex-dayz-mcp.before.toml').write_bytes(block.encode('utf-8'))
(B / 'codex-dayz-mcp.after.toml').write_bytes(newblock.encode('utf-8'))
assert cfg.read_bytes() == raw, 'Concurrent config edit; stop before writing'
assert digest(source.read_bytes()) == source_hash, 'Concurrent MCP source edit'
cfg.write_bytes(new)
assert cfg.read_bytes() == new
provenance = h.resolve_daemon_provenance()
after_cli = subprocess.run([str(binary), 'mcp', 'get', 'dayz-mcp', '--json'], capture_output=True, text=True, timeout=20)
assert after_cli.returncode == 0
codex_after = json.loads(after_cli.stdout)
assert codex_after['enabled'] is True
assert codex_before == codex_after, 'Effective Codex configuration changed'
report = dict(
    status='PASS_REDUNDANT_METADATA_NORMALIZED',
    config_before_sha256=digest(raw), config_after_sha256=digest(new),
    source=str(source), source_sha256=source_hash,
    failing_guard=before_error, counterfactual_registration_equal=True,
    changed_setting='Removed explicit enabled=true from mcp_servers.dayz-mcp only',
    codex_effective_config_exact=True, codex_effective_enabled=True,
    daemon_provenance='PASS_CANONICAL_REGISTRATIONS_AGREE', port=provenance.port,
    credential_values_saved=False, server_source_changed=False,
    daemon_started=False, runtime_started=False,
    limits=['Does not reopen the Codex MCP client or prove tool publication.',
            'Experimental dayz-mcp-130 registration is outside this repair.'])
(B / 'repair.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
