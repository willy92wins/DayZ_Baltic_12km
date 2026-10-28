"""B3G1 receipt delta only. Does not launch or certify an Enforce mission."""
from copy import deepcopy
from datetime import timedelta
import math
from water_query_native_b1_ev112 import instant
from contact_pair_b3g_ev112 import require
import contact_pair_b3g_binding_ev112 as previous


def utc(value):
    require(isinstance(value, str), 'clock_not_utc')
    try:
        parsed = instant(value)
    except ValueError as exc:
        raise ValueError('clock_not_utc') from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0), 'clock_not_utc')
    return parsed


def normalize_launch(raw):
    """Preserve the raw receipt; normalize JSON's exact numeric 600 in a copy."""
    require(isinstance(raw, dict) and isinstance(raw.get('request'), dict)
            and 'wait_for_box_s' in raw['request'], 'queue_duration_missing')
    value = raw['request']['wait_for_box_s']
    require(type(value) in (int, float) and value == 600 and math.isfinite(value),
            'queue_duration_not_exact_600')
    result = deepcopy(raw)
    result['request']['wait_for_box_s'] = 600.0
    return result


def capture_window(receipt):
    fields = ('basis','ready_utc','capture_started_utc','capture_deadline_utc',
              'capture_ended_utc','mission_error_before_capture','run_id','pid',
              'script_log_checked_utc','script_log_sha256')
    require(isinstance(receipt,dict) and all(k in receipt for k in fields), 'window_fields_missing')
    require(isinstance(receipt['run_id'],str) and bool(receipt['run_id'])
            and type(receipt['pid']) is int and receipt['pid'] > 0, 'window_identity')
    digest=receipt['script_log_sha256']
    require(isinstance(digest,str) and len(digest)==64 and all(c in '0123456789abcdef' for c in digest), 'script_log_pin')
    require(receipt['basis'] == 'HOST_UTC_FIRST_SERVER_BOUND_VERSION_OK_FRESH',
            'clock_basis')
    ready, start, deadline, end = [utc(receipt[k]) for k in
        ('ready_utc', 'capture_started_utc', 'capture_deadline_utc', 'capture_ended_utc')]
    require(deadline == ready + timedelta(seconds=180), 'capture_budget')
    require(ready <= start <= end <= deadline, 'capture_outside_window')
    require(ready <= utc(receipt['script_log_checked_utc']) <= start, 'script_check_outside_window')
    require(receipt['mission_error_before_capture'] is False, 'mission_failed')


def identity(deployment, launch, host, after, mcp, capture, cleanup, native_sha, window):
    capture_window(window)
    require(all(k in launch for k in ('run_id',)) and all(k in host for k in ('created_utc','pid'))
            and all(k in capture for k in ('captured_utc','last_write_utc')), 'identity_fields_missing')
    require(window['run_id']==launch['run_id'] and window['pid']==host['pid'], 'window_run_mismatch')
    require(utc(host['created_utc']) <= utc(window['ready_utc']), 'ready_before_process')
    require(utc(capture['captured_utc']) == utc(window['capture_ended_utc']), 'capture_end_binding')
    require(utc(capture['last_write_utc']) <= utc(capture['captured_utc']), 'capture_after_snapshot')
    previous.identity(deployment, normalize_launch(launch), host, after, mcp,
                      capture, cleanup, native_sha)
