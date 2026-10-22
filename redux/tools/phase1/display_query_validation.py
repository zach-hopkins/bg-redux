"""Bounded native display-query contract, including sensitive negative controls."""
import copy
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_stage(directory, *, expected_nonce):
    directory = Path(directory)
    read = lambda name: json.loads((directory/name).read_text(encoding='utf8'))
    host, runtime = read('menu-host-result.json'), read('menu-runtime.json')
    require(isinstance(expected_nonce,str) and len(expected_nonce)==32
        and all(c in '0123456789abcdef' for c in expected_nonce)
        and host.get('nonce') == runtime.get('nonce') == expected_nonce,
        'Display query caller nonce missing/stale')
    require(host.get('completed') is True and host.get('journey') == 'display-query'
        and host.get('callbacks') == 0 and host.get('captures') == 3
        and runtime.get('steps') == runtime.get('planned_steps') == 9,
        'Display query plan incomplete/wrong mode')
    log = (directory/'process.log').read_text(encoding='utf8',errors='replace')
    lines = log.splitlines()
    begin = '[DisplayQueryControl]: begin unsupported-3e rejection'
    end = '[DisplayQueryControl]: end unsupported-3e rejection'
    require(lines.count(begin)==lines.count(end)==1 and lines.index(begin)<lines.index(end),
        'Display query expected error boundary missing/duplicated')
    errors = [(i,line) for i,line in enumerate(lines) if line.startswith(
        ('[Python/ERROR]: Traceback (most recent call last):','[GUIScript/ERROR]: Runtime Error:'))]
    require(len(errors)==1 and errors[0][1].strip()=='[GUIScript/ERROR]: Runtime Error:'
        and lines.index(begin)<errors[0][0]<lines.index(end), 'Display query native callback error')
    checks = runtime['checks']
    verdicts = [r for r in checks if isinstance(r.get('passed'),bool)]
    require(verdicts and all(r['passed'] for r in verdicts), 'Display query runtime assertion failed')
    actions = [r for r in checks if 'action' in r]
    expected_actions = ['display.before','display.rng-control','display.pure','display.after-pure',
        'display.legacy-default','display.legacy-false','display.arm-3e','display.reject-3e','display.final']
    require([r['action'] for r in actions] == expected_actions and [r['step'] for r in actions] == list(range(9)),
        'Display query action inventory missing/reordered')
    require([r['capture'] for r in actions if r.get('capture')] == [1,2,3], 'Display query capture inventory invalid')
    def row(name):
        values = [r for r in checks if r.get('name') == name]
        require(len(values)==1, 'Display query required result missing/duplicated')
        return values[0]
    pure = row('display-query.pure')
    signal = dict(eq14=True,eq12=False,gt13=True,missing=False,control=True)
    require(pure['before_signals'] == pure['after_signals'] == signal,
        'Display query changed original THAC0 trigger contract')
    require(pure['total_api_calls']==144 and pure['repeated_calls']==128 and pure['all_repeats_equal'] is True,
        'Display query repeat coverage absent')
    samples = pure['samples']
    require([(s['actor'],s['hand']) for s in samples] == [(pc,hand) for pc in range(1,5) for hand in (0,1)],
        'Display query actor/hand coverage absent')
    require(all(s['before']==s['after'] and s['repeat_equal'] is True and s['details'] for s in samples),
        'Display query sample mutates stat or lacks result')
    minsc = samples[6]
    require(minsc['actor_name']=='Minsc' and minsc['before']==14
        and minsc['details']['ToHitStats']['Base']==14
        and minsc['details']['ToHitStats']['Ability']==-2
        and minsc['details']['ToHitStats']['Total']==12,
        'Display query misses measured original base14/display12 distinction')
    for name, before in (('display-query.legacy-default',14),('display-query.legacy-false',12)):
        legacy = row(name)
        require(legacy['before']==before and legacy['after']==12
            and legacy['equals_display_result'] is True and legacy['details']==minsc['details'],
            'Display query changed legacy default/result parity')
    require(row('display-query.reject-3e')['error_message']=='Display-only combat details require 2E rules',
        'Display query lacks actual unsupported-rules rejection')
    require(1 <= row('display-query.rng-control')['result'] <= 20, 'Display query RNG control absent')
    paths = sorted(directory.glob('display-query-step-*.json'))
    native = [read(p.name) for p in paths]
    require([r.get('kind') for r in native]==[5,1,2,3,4], 'Display query native observation coverage invalid')
    require([r.get('runtime_step') for r in native]==[2,3,5,6,8], 'Display query native step identity invalid')
    for record in native:
        kind = record['kind']
        require(record.get('nonce')==expected_nonce, 'Display query native nonce mismatch')
        require(record.get('actor_stats_and_cache_bytes_unchanged') is (kind != 2),
            'Display query actor/cache observation or sensitive legacy control failed')
        require(record.get('feature_flag_restored') is True and record.get('controlled_3e_rejection') is (kind == 4),
            'Display query unsupported-rules control/restore failed')
        require(record.get('calling_thread_rng_after_available') is True
            and (kind == 5 or record.get('calling_thread_rng_before_available') is True)
            and record.get('calling_thread_rng_unchanged') is (kind != 5),
            'Display query RNG observation or sensitive draw control failed')
        require(type(record.get('python_step_nanoseconds')) is int and record['python_step_nanoseconds'] >= 0,
            'Display query cost observation missing')
    before, after_pure, final = [read('capture-%d.state.json' % n) for n in (1,2,3)]
    require(before == after_pure, 'Display query pure phase changed collected world')
    require(before['party'][3]['name']=='Minsc' and before['party'][3]['modified_stats'][7]==14,
        'Display query input actor/stat mismatch')
    masked = copy.deepcopy(final)
    for family in ('party','current_area_actors'):
        for index, actor in enumerate(masked[family]):
            if actor['runtime_id'] == before['party'][3]['runtime_id']:
                require(actor['modified_stats'][7]==12, 'Display query legacy control did not expose changed stat')
                actor['modified_stats'][7] = before[family][index]['modified_stats'][7]
    require(masked==before, 'Display query control phase has additional world changes')
    return dict(assertion_passed=True, collected_world_unchanged=False,
        pure_phase_world_unchanged=True, pure_actor_stats_and_cache_bytes_unchanged=True,
        pure_api_calls=144, calling_thread_rng_unchanged_during_query=True,
        explicit_rng_draw_and_legacy_mutation_controls=True, unsupported_3e_control_passed=True,
        legacy_default_unchanged=True, original_script14_display12_matched=True,
        matrix_step_nanoseconds=next(r['python_step_nanoseconds'] for r in native if r['kind']==1),
        whole_run_contains_declared_legacy_and_rng_mutations=True,
        hidden_state_or_other_threads_purity=False, visual_acceptance=False)
