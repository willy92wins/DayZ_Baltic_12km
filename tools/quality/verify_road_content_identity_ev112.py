from __future__ import annotations
import argparse, copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from road_content_identity_io_ev112 import InvalidError, canon, dump_json, is_int_exact, is_sha256, load_pinned_bundle, resolve_pointer, stable_read, strict_json_loads, write_exclusive
ROW_STATES = ['SINGLE_PINNED_CONTENT','SAME_PINNED_CONTENT','DISTINCT_CONTENT','BLOCKED_SHA_CONFLICT','UNRESOLVED','MALFORMED']
METHODS = ['METHOD_BOUND','METHOD_DECLARED','METHOD_UNVERIFIED']
TOP = ['schema','scope','contract_sha256','inputs','status','method_binding_global','counts','table','claims']
ROW = ['name','aliases','source_instances','candidate_instances','historical_state','historical_provider','state','observed_keys','groups','provenances','comparison_evidence','physical_precedence_unknown','historical_issue_pointer','issues','rejected_provenances']
EXPECTED_KEYS = ('references','source_instances','candidate_instances','candidate_delta_instances','single_pinned_content_references','multi_provider_references','historical_conflicts','historical_conflict_instances')
BS = chr(92)
def _norm(value, what='path'):
    if type(value) is not str:
        raise InvalidError(what + ' must be string')
    for ch in value:
        o = ord(ch)
        if o > 127 or o < 32 or o == 127:
            raise InvalidError(what + ' non-ASCII or control in raw value')
    if len(value.encode('ascii')) > 4096:
        raise InvalidError(what + ' too long')
    s = value.replace(BS, '/').lower().strip('/')
    if s == '':
        raise InvalidError(what + ' empty')
    if ':' in s:
        raise InvalidError(what + ' colon')
    for part in s.split('/'):
        if part in ('', '.', '..'):
            raise InvalidError(what + ' bad component')
    return s
def _join(a, b):
    return _norm(a, 'prefix') + '/' + _norm(b, 'entry')
def _validate_bindings(contract, sources):
    need = {'b2a_models','b2a_report','b2a_config','catalog','b4a3_contract','b4a3_summary','road_models','road_entries','b4b0_contract','b4b0_report','b4b0_consumer','b4b0_recovery_receipt','b2a_correction_receipt','b2a_code_adjudication','road_execution_approval','road_report','road_inputs','road_source_table','b2a_code','road_catalog_code','oracles'}
    if set(sources.keys()) != need:
        raise InvalidError('missing or extra required sources')
    def doc(sid):
        v = sources[sid]['parsed']
        if type(v) is not dict:
            raise InvalidError(sid + ' must be object')
        return v
    def sha(sid):
        return sources[sid]['sha256']
    b4b0 = doc('b4b0_report'); consumer = doc('b4b0_consumer'); receipt = doc('b4b0_recovery_receipt'); summ = doc('b4a3_summary'); b4a3c = doc('b4a3_contract'); adj = doc('b2a_code_adjudication'); corr = doc('b2a_correction_receipt'); approval = doc('road_execution_approval'); rreport = doc('road_report'); rinputs = doc('road_inputs')
    if not is_sha256(b4b0.get('contract_sha256')) or b4b0['contract_sha256'] != sha('b4b0_contract'):
        raise InvalidError('b4b0_report contract binding mismatch')
    if not is_sha256(consumer.get('contract_sha256')) or consumer['contract_sha256'] != sha('b4b0_contract'):
        raise InvalidError('b4b0_consumer contract binding mismatch')
    if not is_sha256(receipt.get('source_report_sha256')) or receipt['source_report_sha256'] != sha('b4b0_report'):
        raise InvalidError('recovery receipt source_report mismatch')
    if not is_sha256(receipt.get('consumer_sha256')) or receipt['consumer_sha256'] != sha('b4b0_consumer'):
        raise InvalidError('recovery receipt consumer mismatch')
    pbo = summ.get('pbo')
    if type(pbo) is not dict or type(pbo.get('path')) is not str or not is_sha256(pbo.get('sha256')) or type(pbo.get('prefix')) is not str:
        raise InvalidError('b4a3_summary.pbo invalid')
    if not is_sha256(summ.get('contract_sha')) or summ['contract_sha'] != sha('b4a3_contract'):
        raise InvalidError('b4a3 summary contract mismatch')
    cp = summ.get('catalog_pins')
    if type(cp) is not dict:
        raise InvalidError('b4a3 catalog_pins required')
    for k, sid in (('catalog_sha256','road_entries'),('models_sha256','road_models'),('source_table_sha256','road_source_table')):
        if not is_sha256(cp.get(k)) or cp[k] != sha(sid):
            raise InvalidError('b4a3 catalog pin mismatch ' + k)
    srcs = b4a3c.get('sources')
    if type(srcs) is not dict:
        raise InvalidError('b4a3_contract.sources required')
    for k, sid in (('models','road_models'),('catalog','road_entries'),('source_table','road_source_table')):
        v = srcs.get(k)
        if type(v) is not dict or not is_sha256(v.get('sha256')) or v['sha256'] != sha(sid):
            raise InvalidError('b4a3 source pin mismatch ' + k)
    for k, v in srcs.items():
        if k.startswith('previous:assets/') and (type(v) is not dict or not is_sha256(v.get('sha256'))):
            raise InvalidError('previous asset pin invalid ' + k)
    if not is_sha256(adj.get('final_code_sha256')) or adj['final_code_sha256'] != sha('b2a_code'):
        raise InvalidError('adjudication code pin mismatch')
    ua = corr.get('unchanged_geometry_artifacts')
    if type(ua) is not dict or not is_sha256(ua.get('models.json')) or ua['models.json'] != sha('b2a_models'):
        raise InvalidError('correction models pin mismatch')
    pins = approval.get('pins')
    if type(pins) is not dict or pins.get(sources['road_catalog_code']['path']) != sha('road_catalog_code'):
        raise InvalidError('road execution approval road code pin mismatch')
    if not is_sha256(rreport.get('pbo_sha256')) or rreport['pbo_sha256'] != pbo['sha256']:
        raise InvalidError('road_report pbo pin mismatch')
    norm_inputs = {}
    for k, v in rinputs.items():
        if type(k) is str:
            norm_inputs[k.replace(BS,'/')] = v
    if norm_inputs.get(pbo['path'].replace(BS,'/')) != pbo['sha256']:
        raise InvalidError('road_inputs pbo pin mismatch')
    return pbo
def reconstruct(contract, sources):
    pbo = _validate_bindings(contract, sources)
    def sha(sid):
        return sources[sid]['sha256']
    mb = contract.get('method_binding')
    if type(mb) is not dict:
        raise InvalidError('method_binding required')
    states = {}
    for k in ('b2a','road_catalog'):
        v = mb.get(k)
        if type(v) is not dict or v.get('state') not in METHODS:
            raise InvalidError('method state required ' + k)
        states[k] = v['state']
    b2a_m = states['b2a']; road_m = states['road_catalog']
    b4b0 = sources['b4b0_report']['parsed']
    if type(b4b0) is not dict or type(b4b0.get('table')) is not list or type(b4b0.get('issues')) is not list:
        raise InvalidError('b4b0 table/issues required')
    if len(b4b0['table']) > 10000:
        raise InvalidError('references cap exceeded')
    models = sources['b2a_models']['parsed']; breport = sources['b2a_report']['parsed']; bconfig = sources['b2a_config']['parsed']
    b4a3c = sources['b4a3_contract']['parsed']; rmodels = sources['road_models']['parsed']; rentries = sources['road_entries']['parsed']
    if type(models) is not list or type(rmodels) is not list or type(rentries) is not list or type(breport) is not dict or type(bconfig) is not dict:
        raise InvalidError('source root types')
    pkgs = {}
    if type(breport.get('packages')) is not list:
        raise InvalidError('b2a packages required')
    for pkg in breport['packages']:
        if type(pkg) is not dict or type(pkg.get('path')) is not str or not is_sha256(pkg.get('sha256')) or type(pkg.get('prefix')) is not str:
            raise InvalidError('bad b2a package')
        tup = (pkg['sha256'], pkg['prefix'])
        if pkg['path'] in pkgs and pkgs[pkg['path']] != tup:
            raise InvalidError('conflicting b2a package')
        pkgs[pkg['path']] = tup
    pins = bconfig.get('package_pins')
    if type(pins) is not dict:
        raise InvalidError('package_pins required')
    def cfg_sha(loc):
        v = pins.get(loc)
        if type(v) is str:
            return v
        if type(v) is dict:
            return v.get('sha256')
        return None
    assets = {}
    for k, v in b4a3c['sources'].items():
        if k.startswith('previous:assets/'):
            assets[_norm(k.removeprefix('previous:assets/'), 'asset')] = v['sha256']
    pfx = _norm(pbo['prefix'], 'prefix')
    entries = {}
    for e in rentries:
        if type(e) is not dict or any(k not in e for k in ('name','normalized_name','size','mime','sha256')):
            raise InvalidError('bad road entry')
        if type(e['name']) is not str or type(e['normalized_name']) is not str or not is_sha256(e['sha256']):
            raise InvalidError('bad road entry types')
        rel = _norm(e['normalized_name'], 'entry')
        if rel != _norm(e['name'], 'entry'):
            raise InvalidError('road entry normalized mismatch')
        tup = (e['name'], e['sha256'], e['mime'], e['size'])
        entries.setdefault(rel, {})[canon(tup)] = tup
    models_by_rel = {}
    for i, m in enumerate(rmodels):
        if type(m) is not dict or any(k not in m for k in ('name','sha256','status')) or type(m['name']) is not str or not is_sha256(m['sha256']) or type(m['status']) is not str:
            raise InvalidError('bad road model')
        try:
            nn = _norm(m['name'], 'model')
        except InvalidError as exc:
            raise InvalidError('road_models/' + str(i) + ': invalid name: ' + str(exc)) from exc
        rel = nn[len(pfx) + 1:] if pfx and nn.startswith(pfx + '/') else nn
        models_by_rel.setdefault(rel, []).append((i, m))
    b2a_map = {}; b2a_rej = {}; b2a_bad = set()
    for i, m in enumerate(models):
        if type(m) is not dict or any(k not in m for k in ('name','sha256','package','entry')) or type(m['name']) is not str or type(m['package']) is not str or type(m['entry']) is not str:
            raise InvalidError('bad b2a model')
        try:
            ref = _norm(m['name'], 'name')
        except InvalidError as exc:
            raise InvalidError('b2a_models/' + str(i) + ': invalid name: ' + str(exc)) from exc
        if not is_sha256(m['sha256']):
            b2a_bad.add(ref); continue
        if m['package'] not in pkgs:
            b2a_rej.setdefault(ref, []).append({'source_id':'b2a_models','source_file_sha':sha('b2a_models'),'pointer':'/' + str(i),'reason':'missing_package_lookup'}); continue
        pkg_sha, prefix_raw = pkgs[m['package']]
        if cfg_sha(m['package']) != pkg_sha:
            b2a_rej.setdefault(ref, []).append({'source_id':'b2a_models','source_file_sha':sha('b2a_models'),'pointer':'/' + str(i),'reason':'package_pin_mismatch'}); continue
        try:
            joined = _join(prefix_raw, m['entry'])
        except Exception:
            b2a_bad.add(ref); continue
        if joined != ref:
            b2a_bad.add(ref); continue
        b2a_map.setdefault(ref, []).append(({'source_id':'b2a_models','source_file_sha':sha('b2a_models'),'pointer':'/' + str(i),'package_locator':m['package'],'prefix_raw':prefix_raw,'entry_raw':m['entry'],'method_binding':b2a_m}, {'package':m['package'],'package_sha256':pkg_sha,'prefix':prefix_raw,'entry':m['entry'],'model_sha256':m['sha256']}))
    orig_index = {}
    seen_names = set()
    for i, r in enumerate(b4b0['table']):
        if type(r) is not dict or any(k not in r for k in ('name','aliases','source_instances','candidate_instances','provider','state')):
            raise InvalidError('bad b4b0 row')
        if type(r['name']) is not str or type(r['aliases']) is not list or not is_int_exact(r['source_instances']) or not is_int_exact(r['candidate_instances']) or r['source_instances'] < 0 or r['candidate_instances'] < 0:
            raise InvalidError('bad b4b0 row types')
        if type(r['state']) is not str or any(type(a) is not str for a in r['aliases']):
            raise InvalidError('b4b0 history state/aliases invalid')
        hp = r['provider']
        if hp is not None:
            if type(hp) is not dict or set(hp) != {'package','package_sha256','prefix','entry','model_sha256'} or any(type(hp[k]) is not str for k in hp) or not is_sha256(hp['package_sha256']) or not is_sha256(hp['model_sha256']):
                raise InvalidError('b4b0 historical_provider typed mismatch')
        if r['name'] in seen_names:
            raise InvalidError('duplicate reference')
        seen_names.add(r['name']); orig_index[r['name']] = i
    out_rows = []; raw_counts = []
    for r in sorted(b4b0['table'], key=lambda x: x['name']):
        name = r['name']; orig_idx = orig_index[name]
        cand = list(b2a_map.get(name, [])); rejected = list(b2a_rej.get(name, []))
        malformed = name in b2a_bad
        try:
            if _norm(name, 'n') != name:
                malformed = True
        except Exception:
            malformed = True
        if pfx and name.startswith(pfx + '/'):
            rel = name[len(pfx) + 1:]
            for line_i, m in models_by_rel.get(rel, []):
                ents = list(entries.get(rel, {}).values())
                mtups = {}
                for _i, mm in models_by_rel.get(rel, []):
                    mtups[canon((mm['sha256'], mm['status']))] = (mm['sha256'], mm['status'])
                reason = None
                if len(ents) != 1 or len(mtups) != 1:
                    reason = 'road_entry_or_model_not_unambiguous'
                else:
                    en, eh, mime, sz = ents[0]; mh, st = list(mtups.values())[0]
                    if not is_int_exact(mime) or mime != 0:
                        reason = 'mime_nonzero'
                    elif not is_int_exact(sz) or sz < 0:
                        reason = 'road_entry_size_invalid'
                    elif st != 'READ_STRICT':
                        reason = 'road_not_READ_STRICT'
                    elif mh != eh:
                        reason = 'model_entry_sha_mismatch'
                    elif name in assets and assets[name] != eh:
                        reason = 'previous_asset_sha_mismatch'
                if reason:
                    rejected.append({'source_id':'road_models','source_file_sha':sha('road_models'),'pointer':'/' + str(line_i),'reason':reason})
                else:
                    en, eh, mime, sz = ents[0]
                    cand.append(({'source_id':'road_models','source_file_sha':sha('road_models'),'pointer':'/' + str(line_i),'package_locator':pbo['path'],'prefix_raw':pbo['prefix'],'entry_raw':en,'method_binding':road_m}, {'package':pbo['path'],'package_sha256':pbo['sha256'],'prefix':pbo['prefix'],'entry':en,'model_sha256':eh}))
        cand.sort(key=lambda x: (x[0]['source_id'], int(x[0]['pointer'][1:])))
        provs = [c[0] for c in cand]; raws = [c[1] for c in cand]
        if len(provs) > 64:
            raise InvalidError('provenances cap exceeded')
        distinct_raws = set(canon(x) for x in raws); raw_counts.append(len(distinct_raws))
        ckeys = [(x['package_sha256'], _norm(x['prefix'],'p'), _norm(x['entry'],'e'), x['model_sha256']) for x in raws]
        observed = len(set(ckeys)); by3 = {}
        for ck in ckeys:
            by3.setdefault(ck[:3], set()).add(ck[3])
        blocked = any(len(v) > 1 for v in by3.values())
        groups = []
        if not blocked:
            for ck in sorted(set(ckeys)):
                groups.append({'package_sha256':ck[0],'prefix':ck[1],'entry':ck[2],'model_sha256':ck[3],'provenance_indices':[i for i,c in enumerate(ckeys) if c == ck]})
        if len(groups) > 16:
            raise InvalidError('groups cap exceeded')
        hist = r['provider']; ptr = None; ok = True; issues = []
        if hist is None:
            found = None
            for ii, iss in enumerate(b4b0.get('issues', [])):
                if type(iss) is dict and iss.get('code') == 'PROVIDER_CONFLICT' and iss.get('detail') == 'multiple distinct providers for ' + name:
                    found = ii; break
            if found is not None:
                ptr = '/issues/' + str(found)
            if found is None or len(distinct_raws) < 2:
                ok = False
        else:
            if type(hist) is not dict:
                ok = False
            elif set(hist.keys()) != {'package','package_sha256','prefix','entry','model_sha256'}:
                ok = False
            elif len(distinct_raws) != 1:
                ok = False
            elif canon(raws[0]) != canon(hist):
                ok = False
        if not ok:
            issues.append({'code':'HISTORY_PROVIDER_MISMATCH','detail':'historical provider mismatch for ' + name,'source_id':'b4b0_report','pointer':'/table/' + str(orig_idx)})
        new_unres = False
        if r['source_instances'] == 0:
            if r['state'] != 'NEW_REFERENCE_WITH_B4A3_PIN' or name not in assets or not any(p['source_id'] == 'road_models' for p in provs):
                new_unres = True; issues.append({'code':'NEW_REFERENCE_WITH_B4A3_PIN','detail':'new reference lacks B4A3 pin or road provider for ' + name,'source_id':'b4a3_contract','pointer':'/sources'})
        if not ok or malformed:
            state = 'MALFORMED'
        elif blocked:
            state = 'BLOCKED_SHA_CONFLICT'
        elif not groups or new_unres:
            state = 'UNRESOLVED'
        elif len(distinct_raws) == 1:
            state = 'SINGLE_PINNED_CONTENT'
        elif len(groups) == 1:
            state = 'SAME_PINNED_CONTENT'
        else:
            state = 'DISTINCT_CONTENT'
        ev = []
        for g in groups:
            sids = sorted(set(provs[i]['source_id'] for i in g['provenance_indices']))
            if set(sids) == {'b2a_models','road_models'}:
                kind = 'DECLARED_PIN_MATCH'
            elif sids == ['road_models'] and name in assets:
                kind = 'INHERITED_PIN_MATCH'
            else:
                kind = 'SINGLE_SOURCE_ONLY'
            ev.append({'kind':kind,'source_ids':sids,'provenance_indices':list(g['provenance_indices'])})
        out_rows.append({'name':name,'aliases':list(r['aliases']),'source_instances':r['source_instances'],'candidate_instances':r['candidate_instances'],'historical_state':r['state'],'historical_provider':copy.deepcopy(hist),'state':state,'observed_keys':observed,'groups':groups,'provenances':provs,'comparison_evidence':ev,'physical_precedence_unknown':True,'historical_issue_pointer':ptr,'issues':issues,'rejected_provenances':rejected})
    return out_rows, raw_counts
def verify(contract, contract_sha, sources, inputs, report, report_sha):
    if type(report) is not dict or set(report.keys()) != set(TOP):
        raise InvalidError('report top keys mismatch')
    if report['schema'] != 'road-b4b1-report.v1' or report['scope'] != 'SAVED_CONTENT_IDENTITY_ONLY':
        raise InvalidError('report schema/scope mismatch')
    if not is_sha256(report['contract_sha256']) or report['contract_sha256'] != contract_sha:
        raise InvalidError('report contract binding mismatch')
    if type(report['inputs']) is not list:
        raise InvalidError('report inputs not list')
    for inp in report['inputs']:
        if type(inp) is not dict or set(inp.keys()) != {'source_id','sha256','bytes'} or type(inp['source_id']) is not str or not is_sha256(inp['sha256']) or not is_int_exact(inp['bytes']) or inp['bytes'] < 0:
            raise InvalidError('report input typed mismatch')
    if canon(report['inputs']) != canon(inputs):
        raise InvalidError('report inputs mismatch')
    if type(contract.get('claims')) is not dict or canon(report['claims']) != canon(contract['claims']):
        raise InvalidError('report claims mismatch')
    if type(report['table']) is not list:
        raise InvalidError('report table not list')
    if type(report['counts']) is not dict or set(report['counts'].keys()) != {'references','source_instances','candidate_instances','candidate_delta_instances','single_provider_references','multi_provider_references','accepted_groups','by_state','by_method'}:
        raise InvalidError('counts keys mismatch')
    for k, v in report['counts'].items():
        if k in ('by_state','by_method'):
            continue
        if not is_int_exact(v) or v < 0:
            raise InvalidError('count not exact int ' + k)
    for mapname, enums in (('by_state',ROW_STATES),('by_method',METHODS)):
        mp = report['counts'][mapname]
        if type(mp) is not dict or set(mp.keys()) != set(enums):
            raise InvalidError(mapname + ' keys mismatch')
        for v in mp.values():
            if not is_int_exact(v) or v < 0:
                raise InvalidError(mapname + ' value not exact int')
    for row in report['table']:
        if type(row) is not dict or set(row.keys()) != set(ROW):
            raise InvalidError('row keys mismatch')
        if row['physical_precedence_unknown'] is not True:
            raise InvalidError('physical_precedence_unknown must be true')
        if type(row['name']) is not str or type(row['aliases']) is not list or any(type(a) is not str for a in row['aliases']) or not is_int_exact(row['source_instances']) or not is_int_exact(row['candidate_instances']) or not is_int_exact(row['observed_keys']) or row['source_instances'] < 0 or row['candidate_instances'] < 0 or row['observed_keys'] < 0:
            raise InvalidError('row types mismatch')
        if row['state'] not in ROW_STATES or type(row['historical_state']) is not str:
            raise InvalidError('row state unknown')
        hp = row['historical_provider']
        if hp is not None:
            if type(hp) is not dict or set(hp.keys()) != {'package','package_sha256','prefix','entry','model_sha256'} or not is_sha256(hp['package_sha256']) or not is_sha256(hp['model_sha256']) or any(type(hp[k]) is not str for k in ('package','prefix','entry')):
                raise InvalidError('historical_provider typed mismatch')
        if row['historical_issue_pointer'] is not None and type(row['historical_issue_pointer']) is not str:
            raise InvalidError('historical_issue_pointer type')
        if type(row['groups']) is not list or type(row['provenances']) is not list or type(row['comparison_evidence']) is not list or type(row['issues']) is not list or type(row['rejected_provenances']) is not list:
            raise InvalidError('row lists mismatch')
        if len(row['groups']) > 16 or len(row['provenances']) > 64:
            raise InvalidError('row caps exceeded')
        seen_prov_idx = []
        for g in row['groups']:
            if type(g) is not dict or set(g.keys()) != {'package_sha256','prefix','entry','model_sha256','provenance_indices'}:
                raise InvalidError('group keys mismatch')
            if not is_sha256(g['package_sha256']) or not is_sha256(g['model_sha256']) or type(g['prefix']) is not str or type(g['entry']) is not str:
                raise InvalidError('group typed mismatch')
            if type(g['provenance_indices']) is not list:
                raise InvalidError('provenance_indices not list')
            for ix in g['provenance_indices']:
                if not is_int_exact(ix) or ix < 0 or ix >= len(row['provenances']):
                    raise InvalidError('provenance index typed/range mismatch')
                seen_prov_idx.append(ix)
            if g['provenance_indices'] != sorted(g['provenance_indices']) or len(set(g['provenance_indices'])) != len(g['provenance_indices']):
                raise InvalidError('provenance indices not sorted unique')
        if row['groups'] and sorted(seen_prov_idx) != list(range(len(row['provenances']))):
            raise InvalidError('group provenance coverage incomplete')
        for p in row['provenances']:
            if type(p) is not dict or set(p.keys()) != {'source_id','source_file_sha','pointer','package_locator','prefix_raw','entry_raw','method_binding'}:
                raise InvalidError('provenance keys mismatch')
            if p['method_binding'] not in METHODS or not is_sha256(p['source_file_sha']) or any(type(p[k]) is not str for k in ('source_id','pointer','package_locator','prefix_raw','entry_raw')):
                raise InvalidError('provenance typed mismatch')
            if p['source_id'] not in sources or sources[p['source_id']]['sha256'] != p['source_file_sha']:
                raise InvalidError('provenance source pin mismatch')
            if p['source_id'] in ('b2a_models','road_models'):
                resolved = resolve_pointer(sources[p['source_id']]['parsed'], p['pointer'])
                if type(resolved) is not dict:
                    raise InvalidError('provenance pointer does not resolve to row')
        for ev in row['comparison_evidence']:
            if type(ev) is not dict or set(ev.keys()) != {'kind','source_ids','provenance_indices'} or type(ev['kind']) is not str or type(ev['source_ids']) is not list or type(ev['provenance_indices']) is not list:
                raise InvalidError('evidence typed mismatch')
            for ix in ev['provenance_indices']:
                if not is_int_exact(ix) or ix < 0 or ix >= len(row['provenances']):
                    raise InvalidError('evidence index mismatch')
        for iss in row['issues']:
            if type(iss) is not dict or set(iss.keys()) != {'code','detail','source_id','pointer'} or any(type(iss[k]) is not str for k in iss):
                raise InvalidError('issue typed mismatch')
            if iss['source_id'] == 'b4b0_report':
                resolve_pointer(sources['b4b0_report']['parsed'], iss['pointer'])
        for rp in row['rejected_provenances']:
            if type(rp) is not dict or set(rp.keys()) != {'source_id','source_file_sha','pointer','reason'} or not is_sha256(rp['source_file_sha']) or any(type(rp[k]) is not str for k in ('source_id','pointer','reason')):
                raise InvalidError('rejected provenance typed mismatch')
        if row['historical_issue_pointer'] is not None:
            resolve_pointer(sources['b4b0_report']['parsed'], row['historical_issue_pointer'])
        keys = [(g['package_sha256'], g['prefix'], g['entry'], g['model_sha256']) for g in row['groups']]
        if keys != sorted(keys):
            raise InvalidError('groups not sorted')
    names = [r['name'] for r in report['table']]
    if names != sorted(names) or len(set(names)) != len(names):
        raise InvalidError('table names not sorted unique')
    expected_rows, raw_counts = reconstruct(contract, sources)
    if canon(report['table']) != canon(expected_rows):
        raise InvalidError('table reconstruction mismatch')
    by_state = {s:0 for s in ROW_STATES}; by_method = {m:0 for m in METHODS}
    for row in expected_rows:
        by_state[row['state']] += 1
        for p in row['provenances']:
            by_method[p['method_binding']] += 1
    single = sum(1 for c in raw_counts if c == 1); multi = sum(1 for c in raw_counts if c >= 2)
    counts = {'references':len(expected_rows),'source_instances':sum(r['source_instances'] for r in expected_rows),'candidate_instances':sum(r['candidate_instances'] for r in expected_rows),'candidate_delta_instances':sum(r['candidate_instances'] for r in expected_rows)-sum(r['source_instances'] for r in expected_rows),'single_provider_references':single,'multi_provider_references':multi,'accepted_groups':sum(len(r['groups']) for r in expected_rows),'by_state':by_state,'by_method':by_method}
    if canon(report['counts']) != canon(counts):
        raise InvalidError('counts mismatch')
    exp = contract.get('expected')
    if type(exp) is not dict:
        raise InvalidError('EXPECTED_COUNT_MISMATCH: expected object required')
    actual_expected = {'references':counts['references'],'source_instances':counts['source_instances'],'candidate_instances':counts['candidate_instances'],'candidate_delta_instances':counts['candidate_delta_instances'],'single_pinned_content_references':single,'multi_provider_references':multi,'historical_conflicts':sum(1 for r in expected_rows if r['historical_provider'] is None),'historical_conflict_instances':sum(r['source_instances'] for r in expected_rows if r['historical_provider'] is None)}
    for k in EXPECTED_KEYS:
        if k not in exp or not is_int_exact(exp[k]):
            raise InvalidError('EXPECTED_COUNT_MISMATCH: ' + k + ' missing or not exact int')
        if exp[k] != actual_expected[k]:
            raise InvalidError('EXPECTED_COUNT_MISMATCH: ' + k + ' expected=' + str(exp[k]) + ' actual=' + str(actual_expected[k]))
    worst = METHODS[0]
    for m in METHODS:
        if by_method.get(m,0) > 0 and METHODS.index(m) > METHODS.index(worst):
            worst = m
    if report['method_binding_global'] not in METHODS or report['method_binding_global'] != worst:
        raise InvalidError('method global mismatch')
    if any(r['state'] in ('MALFORMED','UNRESOLVED','DISTINCT_CONTENT','BLOCKED_SHA_CONFLICT') for r in expected_rows):
        status = 'INCONCLUSIVE_SAVED_CONTENT_IDENTITY'
    elif worst == 'METHOD_UNVERIFIED':
        status = 'INCONCLUSIVE_METHOD_BINDING'
    else:
        status = 'SAVED_CONTENT_IDENTITY_VERIFIED_ONLY'
    if report['status'] != status:
        raise InvalidError('status mismatch')
    return status, worst
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--contract', required=True); ap.add_argument('--contract-sha', required=True); ap.add_argument('--report', required=True); ap.add_argument('--output', required=True)
    args = ap.parse_args(argv)
    try:
        contract, csha, sources, inputs = load_pinned_bundle(args.contract, args.contract_sha)
        rdata, rsha, _i = stable_read(args.report)
        if len(rdata) > 16777216:
            raise InvalidError('report too large')
        report = strict_json_loads(rdata)
        status, worst = verify(contract, csha, sources, inputs, report, rsha)
        receipt = {'schema':'road-b4b1-consumer-receipt.v1','state':'VERIFIED_SAVED_CONTENT_DIAGNOSTIC','status':status,'source_report_sha':rsha,'source_report_sha256':rsha,'contract_sha':csha,'contract_sha256':csha,'verification_complete':True,'method_binding_global':worst}
        data = dump_json(receipt)
        if len(data) > 16777216:
            raise InvalidError('receipt too large')
        write_exclusive(args.output, data)
    except Exception as e:
        print('invalid: ' + str(e), file=sys.stderr); return 1
    return 0 if status == 'SAVED_CONTENT_IDENTITY_VERIFIED_ONLY' else 2
if __name__ == '__main__':
    raise SystemExit(main())
