"""Read-only actor/weapon evidence for armed API and actual EE sheet refreshes."""
import copy
import json
from pathlib import Path
import struct

ACTIONS = ('before','rng-control','cold','after-cold','record.open','record.actor1',
    'record.portrait2','record.actor2','record.close','inventory.open','inventory.portrait2','inventory.actor2',
    'inventory.portrait1','inventory.actor1','inventory.close','after-gui','refreshed',
    'legacy-default','legacy-false','final')


def require(value, message):
    if not value:
        raise ValueError(message)


def validate_stage(directory, resolution, *, expected_nonce, expected_input):
    from weapon_query_validation import runtime_guard
    directory = Path(directory)
    read = lambda name: json.loads((directory/name).read_text(encoding='utf8'))
    host, runtime = read('menu-host-result.json'), read('menu-runtime.json')
    require(isinstance(expected_nonce,str) and len(expected_nonce)==32
        and all(c in '0123456789abcdef' for c in expected_nonce)
        and host.get('nonce')==runtime.get('nonce')==expected_nonce,'Armed display nonce missing/stale')
    require(read('armed-input.json')==expected_input,'Armed display caller input drift')
    require(host.get('completed') is True and host.get('journey')=='display-armed'
        and host.get('captures')==8 and host.get('callbacks')==3
        and runtime.get('steps')==runtime.get('planned_steps')==20,'Armed display plan incomplete')
    log=(directory/'process.log').read_text(encoding='utf8',errors='replace')
    require(not any(line.startswith(('[Python/ERROR]: Traceback (most recent call last):',
        '[GUIScript/ERROR]: Runtime Error:')) for line in log.splitlines()),'Armed display callback error')
    checks=runtime['checks'];verdicts=[r for r in checks if isinstance(r.get('passed'),bool)]
    require(verdicts and all(r['passed'] for r in verdicts),'Armed display runtime assertion failed')
    actions=[r for r in checks if 'action' in r]
    require([r['action'] for r in actions]==['armed.'+s for s in ACTIONS]
        and [r['step'] for r in actions]==list(range(20)),'Armed display actions missing/reordered')
    require([r['capture'] for r in actions if r.get('capture')]==list(range(1,9)),
        'Armed display captures missing/reordered')
    def row(name):
        values=[r for r in checks if r.get('name')==name]
        require(len(values)==1,'Armed display required result missing/duplicated')
        return values[0]
    before=read('before.state.json');observer=read('before.observer.json')
    guard=runtime_guard(expected_input['row'],expected_input['item_metadata'],before,read('before.weapons.json'))
    cold, refreshed=row('armed.matrix.cold'),row('armed.matrix.refreshed')
    require(1<=row('armed.rng-control')['result']<=20,'Armed display die-roll control missing')
    samples=cold['samples']
    require(samples==refreshed['samples'],'Armed display refresh changed queried results')
    for matrix in (cold,refreshed):
        require(matrix['api_calls']==128 and matrix['repeats']==32
            and [(s['actor'],s['hand']) for s in matrix['samples']]==[(pc,h) for pc in (1,2) for h in (0,1)],
            'Armed display repeat/actor/hand coverage missing')
        require(all(s['before']==s['after']==before['party'][s['actor']-1]['modified_stats'][7]
            and s['repeat_equal'] is True and s['details'] for s in matrix['samples']),
            'Armed display query changed stat or repeated result')
    spec=expected_input['row']['spec'];dual=bool(spec['off'] and not spec['off'].startswith('shld'))
    require(samples[0]['dual']==samples[1]['dual']==dual,'Armed display actual dual-wield mode differs')
    for hand in (0,1):
        sample=samples[hand];effective=hand if dual else 0;cache=guard['cache']['hands'][effective]
        require((sample['item'] or '').lower()==cache['item'].lower()
            and sample['details']['Slot']==cache['slot'] and sample['details']['Flags']==cache['wflags']
            and sample['details']['Enchantment']==cache['enchantment'],
            'Armed display returned wrong equipped hand/item/header')
    sheets=[r for r in checks if r.get('name')=='armed.sheet']
    require([(r['pack'],r['actor']) for r in sheets]==[('GUIREC',1),('GUIREC',2),('GUIINV',2),('GUIINV',1)],
        'Armed display Record/Inventory/selection coverage missing')
    def field(ui,pack,cid):
        values=[c for c in ui['controls'] if c['pack']==pack and c['window']==2 and c['id']==cid and c['visible']]
        require(len(values)==1,'Armed display visible control absent/ambiguous')
        return values[0]['text']
    for number in range(1,9):
        bmp=(directory/('capture-%d.bmp'%number)).read_bytes()
        require(len(bmp)>54 and bmp[:2]==b'BM' and struct.unpack_from('<I',bmp,2)[0]==len(bmp)
            and list(struct.unpack_from('<ii',bmp,18))==list(resolution),'Armed display BMP size/resolution invalid')
        state=read('capture-%d.state.json'%number)
        if number<8:
            expected=copy.deepcopy(before);expected['selection']={4:2,5:2}.get(number,1)
            require(state==expected,'Armed display pure/GUI phase changed collected world')
            require(read('capture-%d.observer.json'%number)==observer,'Armed display pure/GUI phase changed caches')
        if number in (3,4,5,6):
            sheet=sheets[number-3];pc=sheet['actor'];pack=sheet['pack'];ui=read('capture-%d.ui.json'%number)
            details=[s['details'] for s in samples if s['actor']==pc]
            if not samples[(pc-1)*2]['dual']:details=details[:1]
            headline='/'.join(str(d['ToHitStats']['Total']) for d in details)
            require(sheet['details']==details and sheet['headline']==headline
                and field(ui,pack,0x10000040 if pack=='GUIREC' else 0x10000055)==headline
                and field(ui,pack,0x1000000e if pack=='GUIREC' else 0x10000032)==before['party'][pc-1]['name'],
                'Armed display actual sheet identity/headline/parity failed')
            ids=(53,54,55,56) if pack=='GUIREC' else (77,78,79,80)
            require(len(sheet['panels'])==4 and all(sheet['panels'])
                and [field(ui,pack,cid) for cid in ids]==sheet['panels'],
                'Armed display actual visible panels differ')
    callbacks=[read(p.name) for p in sorted(directory.glob('callback-*.json')) if p.stem.split('-')[-1].isdigit()]
    require([(r.get('sequence'),r.get('runtime_step'),r.get('pack'),r.get('window'),r.get('control')) for r in callbacks]
        ==[(1,7,'PORTWIN',0,1),(2,11,'PORTWIN',0,1),(3,13,'PORTWIN',0,0)],'Armed display registered portrait callbacks missing/wrong')
    for callback in callbacks:
        require(callback.get('nonce')==expected_nonce and callback.get('performed') is True,'Armed display callback identity stale')
        n=callback['sequence']
        for side in ('before','after'):
            state=read('callback-%d-%s.state.json'%(n,side));state['selection']=before['selection']
            require(state==before and read('callback-%d-%s.observer.json'%(n,side))==observer,
                'Armed display portrait callback changed world/cache')
    legacy_default,legacy_false=row('armed.legacy-default'),row('armed.legacy-false')
    for legacy in (legacy_default,legacy_false):
        require(legacy['equals_display_result'] is True
            and [(s['actor'],s['hand']) for s in legacy['samples']]==[(pc,h) for pc in (1,2) for h in (0,1)]
            and [s['details'] for s in legacy['samples']]==[s['details'] for s in samples],
            'Armed display legacy omitted/False parity failed')
    expected=copy.deepcopy(before)
    for pc in (1,2):
        last=legacy_false['samples'][pc*2-1]
        require(last['after']==(last['details']['ToHitStats']['Total']&0xffffffff),
            'Armed display legacy mutation control inconsistent')
        identity=before['party'][pc-1]['runtime_id']
        for family in ('party','current_area_actors'):
            for actor in expected[family]:
                if actor['runtime_id']==identity:actor['modified_stats'][7]=last['after']
    require(read('capture-8.state.json')==read('after.state.json')==expected,
        'Armed display legacy phase has additional world changes')
    final_observer=read('after.observer.json')
    for pc in (1,2):
        values=[a for a in final_observer['actors'] if a['party_index']==pc]
        require(len(values)==1 and (values[0]['cached_thac0']&0xffffffff)==legacy_false['samples'][pc*2-1]['after'],
            'Armed display legacy final cache/result inconsistent')
    native=[read(p.name) for p in sorted(directory.glob('display-query-step-*.json'))]
    require([r.get('kind') for r in native]==[5,1,1,2,3]
        and [r.get('runtime_step') for r in native]==[2,3,17,18,19],'Armed display native boundary coverage wrong')
    require((expected==before and final_observer==observer) or native[3]['actor_stats_and_cache_bytes_unchanged'] is False,
        'Armed display legacy mutation control insensitive')
    for r in native:
        kind=r['kind']
        require(r.get('nonce')==expected_nonce and type(r.get('actor_stats_and_cache_bytes_unchanged')) is bool,
            'Armed display native identity/byte observation missing')
        require(kind==2 or r['actor_stats_and_cache_bytes_unchanged'] is True,
            'Armed display query/GUI follow-up changed actor/cache bytes')
        require(r.get('calling_thread_rng_after_available') is True
            and (kind==5 or r.get('calling_thread_rng_before_available') is True)
            and r.get('calling_thread_rng_unchanged') is (kind!=5),'Armed display RNG/control observation failed')
        require(r.get('feature_flag_restored') is True and r.get('controlled_3e_rejection') is False,
            'Armed display feature flag differs')
        require(type(r.get('python_step_nanoseconds')) is int and r['python_step_nanoseconds']>=0,
            'Armed display cost observation missing')
    return dict(assertion_passed=True,pure_phase_world_unchanged=True,collected_world_unchanged=False,
        case_id=spec['id'],actual_dual_wield=dual,actual_ranged=bool(spec['ammo']),
        actual_items=guard['inventory'],display_api_calls=256,sheet_observations=4,portrait_callbacks=3,
        legacy_result_parity=True,legacy_control_changed_actor_bytes=not native[3]['actor_stats_and_cache_bytes_unchanged'],
        matrix_step_nanoseconds=[r['python_step_nanoseconds'] for r in native if r['kind']==1],
        pure_query_actor_bytes_and_calling_thread_rng_unchanged=True,gui_collected_world_and_caches_unchanged=True,
        original_armed_combat_math_oracle=False,hidden_state_or_other_threads_purity=False,visual_acceptance=False)
