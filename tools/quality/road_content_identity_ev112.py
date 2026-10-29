from __future__ import annotations
import argparse, copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from road_content_identity_io_ev112 import InvalidError, canon, dump_json, is_int_exact, is_sha256, load_pinned_bundle, normalize_join, normalize_path_value, write_exclusive
ROW_STATES = ['SINGLE_PINNED_CONTENT','SAME_PINNED_CONTENT','DISTINCT_CONTENT','BLOCKED_SHA_CONFLICT','UNRESOLVED','MALFORMED']
METHODS = ['METHOD_BOUND','METHOD_DECLARED','METHOD_UNVERIFIED']
EXPECTED_KEYS = ('references','source_instances','candidate_instances','candidate_delta_instances','single_pinned_content_references','multi_provider_references','historical_conflicts','historical_conflict_instances')
def _sha(sources, sid):
    return sources[sid]['sha256']
def _validate_bindings(contract, sources):
    need = {'b2a_models','b2a_report','b2a_config','catalog','b4a3_contract','b4a3_summary','road_models','road_entries','b4b0_contract','b4b0_report','b4b0_consumer','b4b0_recovery_receipt','b2a_correction_receipt','b2a_code_adjudication','road_execution_approval','road_report','road_inputs','road_source_table','b2a_code','road_catalog_code','oracles'}
    if set(sources.keys()) != need:
        raise InvalidError('missing or extra required sources')
    def doc(sid):
        v = sources[sid]['parsed']
        if type(v) is not dict:
            raise InvalidError(sid + ' must be object')
        return v
    b4b0 = doc('b4b0_report'); consumer = doc('b4b0_consumer'); receipt = doc('b4b0_recovery_receipt')
    summ = doc('b4a3_summary'); b4a3c = doc('b4a3_contract'); adj = doc('b2a_code_adjudication'); corr = doc('b2a_correction_receipt')
    approval = doc('road_execution_approval'); rreport = doc('road_report'); rinputs = doc('road_inputs')
    if not is_sha256(b4b0.get('contract_sha256')) or b4b0['contract_sha256'] != _sha(sources,'b4b0_contract'):
        raise InvalidError('b4b0_report contract binding mismatch')
    if not is_sha256(consumer.get('contract_sha256')) or consumer['contract_sha256'] != _sha(sources,'b4b0_contract'):
        raise InvalidError('b4b0_consumer contract binding mismatch')
    if not is_sha256(receipt.get('source_report_sha256')) or receipt['source_report_sha256'] != _sha(sources,'b4b0_report'):
        raise InvalidError('recovery receipt source_report mismatch')
    if not is_sha256(receipt.get('consumer_sha256')) or receipt['consumer_sha256'] != _sha(sources,'b4b0_consumer'):
        raise InvalidError('recovery receipt consumer mismatch')
    pbo = summ.get('pbo')
    if type(pbo) is not dict or type(pbo.get('path')) is not str or not is_sha256(pbo.get('sha256')) or type(pbo.get('prefix')) is not str:
        raise InvalidError('b4a3_summary.pbo invalid')
    if not is_sha256(summ.get('contract_sha')) or summ['contract_sha'] != _sha(sources,'b4a3_contract'):
        raise InvalidError('b4a3 summary contract mismatch')
    cp = summ.get('catalog_pins')
    if type(cp) is not dict:
        raise InvalidError('b4a3 catalog_pins required')
    for k, sid in (('catalog_sha256','road_entries'),('models_sha256','road_models'),('source_table_sha256','road_source_table')):
        if not is_sha256(cp.get(k)) or cp[k] != _sha(sources,sid):
            raise InvalidError('b4a3 catalog pin mismatch ' + k)
    srcs = b4a3c.get('sources')
    if type(srcs) is not dict:
        raise InvalidError('b4a3_contract.sources required')
    for k, sid in (('models','road_models'),('catalog','road_entries'),('source_table','road_source_table')):
        v = srcs.get(k)
        if type(v) is not dict or not is_sha256(v.get('sha256')) or v['sha256'] != _sha(sources,sid):
            raise InvalidError('b4a3 source pin mismatch ' + k)
    for k, v in srcs.items():
        if k.startswith('previous:assets/'):
            if type(v) is not dict or not is_sha256(v.get('sha256')):
                raise InvalidError('previous asset pin invalid ' + k)
    if not is_sha256(adj.get('final_code_sha256')) or adj['final_code_sha256'] != _sha(sources,'b2a_code'):
        raise InvalidError('adjudication code pin mismatch')
    ua = corr.get('unchanged_geometry_artifacts')
    if type(ua) is not dict or not is_sha256(ua.get('models.json')) or ua['models.json'] != _sha(sources,'b2a_models'):
        raise InvalidError('correction models pin mismatch')
    pins = approval.get('pins')
    if type(pins) is not dict or pins.get(sources['road_catalog_code']['path']) != _sha(sources,'road_catalog_code'):
        raise InvalidError('road execution approval road code pin mismatch')
    if not is_sha256(rreport.get('pbo_sha256')) or rreport['pbo_sha256'] != pbo['sha256']:
        raise InvalidError('road_report pbo pin mismatch')
    norm_inputs = {}
    for k, v in rinputs.items():
        if type(k) is str:
            norm_inputs[k.replace(chr(92),'/')] = v
    if norm_inputs.get(pbo['path'].replace(chr(92),'/')) != pbo['sha256']:
        raise InvalidError('road_inputs pbo pin mismatch')
    return pbo
def _method_states(contract):
    mb = contract.get('method_binding')
    if type(mb) is not dict:
        raise InvalidError('method_binding required')
    out = {}
    for k in ('b2a','road_catalog'):
        v = mb.get(k)
        if type(v) is not dict or v.get('state') not in METHODS:
            raise InvalidError('method_binding state required for ' + k)
        out[k] = v['state']
    return out['b2a'], out['road_catalog']
def _check_expected(contract, actual):
    exp = contract.get('expected')
    if type(exp) is not dict:
        raise InvalidError('EXPECTED_COUNT_MISMATCH: expected object required')
    for k in EXPECTED_KEYS:
        if k not in exp or not is_int_exact(exp[k]):
            raise InvalidError('EXPECTED_COUNT_MISMATCH: ' + k + ' missing or not exact int')
        if exp[k] != actual[k]:
            raise InvalidError('EXPECTED_COUNT_MISMATCH: ' + k + ' expected=' + str(exp[k]) + ' actual=' + str(actual[k]))
def build_report(contract, contract_sha, sources, inputs):
    pbo = _validate_bindings(contract, sources)
    b2a_method, road_method = _method_states(contract)
    if type(contract.get('claims')) is not dict:
        raise InvalidError('contract claims required')
    b4b0_report = sources['b4b0_report']['parsed']
    if type(b4b0_report.get('table')) is not list or type(b4b0_report.get('issues')) is not list:
        raise InvalidError('b4b0_report table/issues required')
    table_in = b4b0_report['table']
    if len(table_in) > 10000:
        raise InvalidError('references cap exceeded')
    b2a_models = sources['b2a_models']['parsed']; b2a_report = sources['b2a_report']['parsed']; b2a_config = sources['b2a_config']['parsed']
    road_models = sources['road_models']['parsed']; road_entries = sources['road_entries']['parsed']; b4a3_contract = sources['b4a3_contract']['parsed']
    if type(b2a_models) is not list or type(road_models) is not list or type(road_entries) is not list:
        raise InvalidError('list inputs wrong root types')
    if type(b2a_report) is not dict or type(b2a_config) is not dict:
        raise InvalidError('b2a report/config wrong root types')
    packages = {}
    pkg_list = b2a_report.get('packages')
    if type(pkg_list) is not list:
        raise InvalidError('b2a packages required')
    for pkg in pkg_list:
        if type(pkg) is not dict or type(pkg.get('path')) is not str or not is_sha256(pkg.get('sha256')) or type(pkg.get('prefix')) is not str:
            raise InvalidError('bad b2a package row')
        tup = (pkg['sha256'], pkg['prefix'])
        if pkg['path'] in packages and packages[pkg['path']] != tup:
            raise InvalidError('conflicting b2a package')
        packages[pkg['path']] = tup
    pin_map = b2a_config.get('package_pins')
    if type(pin_map) is not dict:
        raise InvalidError('b2a config package_pins required')
    def config_sha(locator):
        if locator not in pin_map:
            return None
        v = pin_map[locator]
        if type(v) is str:
            return v
        if type(v) is dict:
            return v.get('sha256')
        return None
    asset_pins = {}
    for k, v in b4a3_contract['sources'].items():
        if k.startswith('previous:assets/'):
            asset_pins[normalize_path_value(k.removeprefix('previous:assets/'), 'asset')] = v['sha256']
    pbo_prefix_norm = normalize_path_value(pbo['prefix'], 'prefix')
    entry_by = {}
    for e in road_entries:
        if type(e) is not dict:
            raise InvalidError('bad road entry')
        for k in ('name','normalized_name','size','mime','sha256'):
            if k not in e:
                raise InvalidError('road entry missing ' + k)
        if type(e['name']) is not str or type(e['normalized_name']) is not str or not is_sha256(e['sha256']):
            raise InvalidError('bad road entry types')
        rel = normalize_path_value(e['normalized_name'], 'entry')
        if rel != normalize_path_value(e['name'], 'entry'):
            raise InvalidError('road entry normalized mismatch')
        tup = (e['name'], e['sha256'], e['mime'], e['size'])
        entry_by.setdefault(rel, {})[canon(tup)] = tup
    model_by_rel = {}
    for idx, m in enumerate(road_models):
        if type(m) is not dict or 'name' not in m or 'sha256' not in m or 'status' not in m:
            raise InvalidError('bad road model row')
        if type(m['name']) is not str or not is_sha256(m['sha256']) or type(m['status']) is not str:
            raise InvalidError('bad road model types')
        try:
            nname = normalize_path_value(m['name'], 'model name')
        except InvalidError as exc:
            raise InvalidError('road_models/' + str(idx) + ': invalid name: ' + str(exc)) from exc
        if pbo_prefix_norm and nname.startswith(pbo_prefix_norm + '/'):
            rel = nname[len(pbo_prefix_norm) + 1:]
        else:
            rel = nname
        model_by_rel.setdefault(rel, []).append((idx, m))
    b2a_by_ref = {}; b2a_rejected = {}; b2a_malformed = set()
    for idx, m in enumerate(b2a_models):
        if type(m) is not dict or any(k not in m for k in ('name','sha256','package','entry')):
            raise InvalidError('bad b2a model row')
        if type(m['name']) is not str or type(m['package']) is not str or type(m['entry']) is not str:
            raise InvalidError('bad b2a model types')
        try:
            ref = normalize_path_value(m['name'], 'model name')
        except InvalidError as exc:
            raise InvalidError('b2a_models/' + str(idx) + ': invalid name: ' + str(exc)) from exc
        if not is_sha256(m['sha256']):
            b2a_malformed.add(ref); continue
        if m['package'] not in packages:
            b2a_rejected.setdefault(ref, []).append({'source_id':'b2a_models','source_file_sha':_sha(sources,'b2a_models'),'pointer':'/' + str(idx),'reason':'missing_package_lookup'}); continue
        pkg_sha, prefix_raw = packages[m['package']]
        if config_sha(m['package']) != pkg_sha:
            b2a_rejected.setdefault(ref, []).append({'source_id':'b2a_models','source_file_sha':_sha(sources,'b2a_models'),'pointer':'/' + str(idx),'reason':'package_pin_mismatch'}); continue
        try:
            joined = normalize_join(prefix_raw, m['entry'])
        except Exception:
            b2a_malformed.add(ref); continue
        if joined != ref:
            b2a_malformed.add(ref); continue
        prov = {'source_id':'b2a_models','source_file_sha':_sha(sources,'b2a_models'),'pointer':'/' + str(idx),'package_locator':m['package'],'prefix_raw':prefix_raw,'entry_raw':m['entry'],'method_binding':b2a_method}
        raw = {'package':m['package'],'package_sha256':pkg_sha,'prefix':prefix_raw,'entry':m['entry'],'model_sha256':m['sha256']}
        b2a_by_ref.setdefault(joined, []).append((prov, raw))
    names = []
    for r in table_in:
        if type(r) is not dict:
            raise InvalidError('b4b0 table row not object')
        for k in ('name','aliases','source_instances','candidate_instances','provider','state'):
            if k not in r:
                raise InvalidError('b4b0 row missing ' + k)
        if type(r['name']) is not str or type(r['aliases']) is not list or not is_int_exact(r['source_instances']) or not is_int_exact(r['candidate_instances']) or r['source_instances'] < 0 or r['candidate_instances'] < 0:
            raise InvalidError('b4b0 row bad types')
        if type(r['state']) is not str or any(type(a) is not str for a in r['aliases']):
            raise InvalidError('b4b0 history state/aliases invalid')
        hp = r['provider']
        if hp is not None:
            if type(hp) is not dict or set(hp) != {'package','package_sha256','prefix','entry','model_sha256'} or any(type(hp[k]) is not str for k in hp) or not is_sha256(hp['package_sha256']) or not is_sha256(hp['model_sha256']):
                raise InvalidError('b4b0 historical_provider typed mismatch')
        names.append(r['name'])
    if len(set(names)) != len(names):
        raise InvalidError('duplicate reference in b4b0 table')
    orig_index = {}
    for i, r in enumerate(table_in):
        orig_index[r['name']] = i
    issues_b4b0 = b4b0_report['issues']
    rows = []; raw_counts = []
    for r in sorted(table_in, key=lambda x: x['name']):
        name = r['name']; ridx = orig_index[name]
        candidates = list(b2a_by_ref.get(name, [])); rejected = list(b2a_rejected.get(name, []))
        malformed = name in b2a_malformed
        try:
            if normalize_path_value(name, 'name') != name:
                malformed = True
        except Exception:
            malformed = True
        if pbo_prefix_norm and name.startswith(pbo_prefix_norm + '/'):
            rel = name[len(pbo_prefix_norm) + 1:]
            for line_idx, m in model_by_rel.get(rel, []):
                entries = list(entry_by.get(rel, {}).values())
                models_here = model_by_rel.get(rel, [])
                model_tuples = {}
                for _i, mm in models_here:
                    model_tuples[canon((mm['sha256'], mm['status']))] = (mm['sha256'], mm['status'])
                reason = None
                if len(entries) != 1 or len(model_tuples) != 1:
                    reason = 'road_entry_or_model_not_unambiguous'
                else:
                    ename, esha, mime, esize = entries[0]; msha, mstatus = list(model_tuples.values())[0]
                    if not is_int_exact(mime) or mime != 0:
                        reason = 'mime_nonzero'
                    elif not is_int_exact(esize) or esize < 0:
                        reason = 'road_entry_size_invalid'
                    elif mstatus != 'READ_STRICT':
                        reason = 'road_not_READ_STRICT'
                    elif msha != esha:
                        reason = 'model_entry_sha_mismatch'
                    elif name in asset_pins and asset_pins[name] != esha:
                        reason = 'previous_asset_sha_mismatch'
                if reason:
                    rejected.append({'source_id':'road_models','source_file_sha':_sha(sources,'road_models'),'pointer':'/' + str(line_idx),'reason':reason})
                else:
                    ename, esha, mime, esize = entries[0]
                    prov = {'source_id':'road_models','source_file_sha':_sha(sources,'road_models'),'pointer':'/' + str(line_idx),'package_locator':pbo['path'],'prefix_raw':pbo['prefix'],'entry_raw':ename,'method_binding':road_method}
                    raw = {'package':pbo['path'],'package_sha256':pbo['sha256'],'prefix':pbo['prefix'],'entry':ename,'model_sha256':esha}
                    candidates.append((prov, raw))
        candidates.sort(key=lambda x: (x[0]['source_id'], int(x[0]['pointer'][1:])))
        provenances = [c[0] for c in candidates]; raws = [c[1] for c in candidates]
        if len(provenances) > 64:
            raise InvalidError('provenances cap exceeded for ' + name)
        raw_set = set(canon(x) for x in raws); distinct_raw = len(raw_set); raw_counts.append(distinct_raw)
        content_keys = []
        for raw in raws:
            content_keys.append((raw['package_sha256'], normalize_path_value(raw['prefix'],'prefix'), normalize_path_value(raw['entry'],'entry'), raw['model_sha256']))
        observed = len(set(content_keys))
        by3 = {}
        for ck in content_keys:
            by3.setdefault(ck[:3], set()).add(ck[3])
        blocked = any(len(v) > 1 for v in by3.values())
        groups = []
        if not blocked:
            for ck in sorted(set(content_keys)):
                groups.append({'package_sha256':ck[0],'prefix':ck[1],'entry':ck[2],'model_sha256':ck[3],'provenance_indices':[i for i,c in enumerate(content_keys) if c == ck]})
        if len(groups) > 16:
            raise InvalidError('groups cap exceeded for ' + name)
        hist = r['provider']; hist_state = r['state']; issue_ptr = None; hist_ok = True; row_issues = []
        if hist is None:
            found = None
            for ii, iss in enumerate(issues_b4b0):
                if type(iss) is dict and iss.get('code') == 'PROVIDER_CONFLICT' and iss.get('detail') == 'multiple distinct providers for ' + name:
                    found = ii; break
            if found is not None:
                issue_ptr = '/issues/' + str(found)
            if found is None or distinct_raw < 2:
                hist_ok = False
        else:
            if type(hist) is not dict:
                hist_ok = False
            elif set(hist.keys()) != {'package','package_sha256','prefix','entry','model_sha256'}:
                hist_ok = False
            elif distinct_raw != 1:
                hist_ok = False
            elif canon(raws[0]) != canon(hist):
                hist_ok = False
        if not hist_ok:
            row_issues.append({'code':'HISTORY_PROVIDER_MISMATCH','detail':'historical provider mismatch for ' + name,'source_id':'b4b0_report','pointer':'/table/' + str(ridx)})
        new_unresolved = False
        if r['source_instances'] == 0:
            road_ok = any(p['source_id'] == 'road_models' for p in provenances) and name in asset_pins
            if hist_state != 'NEW_REFERENCE_WITH_B4A3_PIN' or not road_ok:
                new_unresolved = True
                row_issues.append({'code':'NEW_REFERENCE_WITH_B4A3_PIN','detail':'new reference lacks B4A3 pin or road provider for ' + name,'source_id':'b4a3_contract','pointer':'/sources'})
        if not hist_ok or malformed:
            state = 'MALFORMED'
        elif blocked:
            state = 'BLOCKED_SHA_CONFLICT'
        elif not groups:
            state = 'UNRESOLVED'
        elif new_unresolved:
            state = 'UNRESOLVED'
        elif distinct_raw == 1:
            state = 'SINGLE_PINNED_CONTENT'
        elif len(groups) == 1:
            state = 'SAME_PINNED_CONTENT'
        else:
            state = 'DISTINCT_CONTENT'
        evidence = []
        for g in groups:
            sids = sorted(set(provenances[i]['source_id'] for i in g['provenance_indices']))
            if set(sids) == {'b2a_models','road_models'}:
                kind = 'DECLARED_PIN_MATCH'
            elif sids == ['road_models'] and name in asset_pins:
                kind = 'INHERITED_PIN_MATCH'
            else:
                kind = 'SINGLE_SOURCE_ONLY'
            evidence.append({'kind':kind,'source_ids':sids,'provenance_indices':list(g['provenance_indices'])})
        rows.append({'name':name,'aliases':list(r['aliases']),'source_instances':r['source_instances'],'candidate_instances':r['candidate_instances'],'historical_state':hist_state,'historical_provider':copy.deepcopy(hist),'state':state,'observed_keys':observed,'groups':groups,'provenances':provenances,'comparison_evidence':evidence,'physical_precedence_unknown':True,'historical_issue_pointer':issue_ptr,'issues':row_issues,'rejected_provenances':rejected})
    by_state = {s:0 for s in ROW_STATES}; by_method = {m:0 for m in METHODS}
    for row in rows:
        by_state[row['state']] += 1
        for p in row['provenances']:
            by_method[p['method_binding']] += 1
    single = sum(1 for c in raw_counts if c == 1); multi = sum(1 for c in raw_counts if c >= 2)
    counts = {'references':len(rows),'source_instances':sum(r['source_instances'] for r in rows),'candidate_instances':sum(r['candidate_instances'] for r in rows),'candidate_delta_instances':sum(r['candidate_instances'] for r in rows)-sum(r['source_instances'] for r in rows),'single_provider_references':single,'multi_provider_references':multi,'accepted_groups':sum(len(r['groups']) for r in rows),'by_state':by_state,'by_method':by_method}
    actual_expected = {'references':counts['references'],'source_instances':counts['source_instances'],'candidate_instances':counts['candidate_instances'],'candidate_delta_instances':counts['candidate_delta_instances'],'single_pinned_content_references':single,'multi_provider_references':multi,'historical_conflicts':sum(1 for r in rows if r['historical_provider'] is None),'historical_conflict_instances':sum(r['source_instances'] for r in rows if r['historical_provider'] is None)}
    _check_expected(contract, actual_expected)
    worst = METHODS[0]
    for m in METHODS:
        if by_method.get(m,0) > 0 and METHODS.index(m) > METHODS.index(worst):
            worst = m
    if any(r['state'] in ('MALFORMED','UNRESOLVED','DISTINCT_CONTENT','BLOCKED_SHA_CONFLICT') for r in rows):
        status = 'INCONCLUSIVE_SAVED_CONTENT_IDENTITY'
    elif worst == 'METHOD_UNVERIFIED':
        status = 'INCONCLUSIVE_METHOD_BINDING'
    else:
        status = 'SAVED_CONTENT_IDENTITY_VERIFIED_ONLY'
    return {'schema':'road-b4b1-report.v1','scope':'SAVED_CONTENT_IDENTITY_ONLY','contract_sha256':contract_sha,'inputs':inputs,'status':status,'method_binding_global':worst,'counts':counts,'table':rows,'claims':copy.deepcopy(contract['claims'])}
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--contract', required=True); ap.add_argument('--contract-sha', required=True); ap.add_argument('--output', required=True)
    args = ap.parse_args(argv)
    try:
        contract, csha, sources, inputs = load_pinned_bundle(args.contract, args.contract_sha)
        report = build_report(contract, csha, sources, inputs)
        data = dump_json(report)
        if len(data) > 16777216:
            raise InvalidError('report exceeds byte cap')
        write_exclusive(args.output, data)
    except Exception as e:
        print('invalid: ' + str(e), file=sys.stderr); return 1
    return 0 if report['status'] == 'SAVED_CONTENT_IDENTITY_VERIFIED_ONLY' else 2
if __name__ == '__main__':
    raise SystemExit(main())
