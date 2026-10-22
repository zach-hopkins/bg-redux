"""Strict intended-identity Erase contracts; independent of GemRB/runtime callbacks."""
import copy
import spellbook_operation_validation as base
from spellbook_operation_validation import (wire_spellbooks, wire_state_guard, page,
    equal_except_selection, callback_game_boundary, field, book_guard, caster_surfaces)

TARGET='SPWI213'
CASE=dict(name='mage',pc=2,pack='GUIMG',kind=1,level=1,ref=TARGET,known=2,modal=101,tabs=61,count=9)

def expected_plan(mode,policy=None):
    if mode not in ('operate','reload'):raise ValueError('Unsupported Erase mode')
    plan=['mage.portrait','mage.open','mage.level','mage.before']
    if mode=='operate':plan+=['mage.info','mage.information','mage.erase','mage.confirmation',
        'mage.cancel','mage.after-cancel','mage.erase-again','mage.confirmation-again','mage.confirm','mage.after-erase']
    return plan+['mage.close','leader-portrait']

def terminal_identity(host,runtime,nonce,mode,policy):
    if len(nonce)!=32 or any(c not in '0123456789abcdef' for c in nonce):raise ValueError('Invalid caller nonce')
    if policy not in ('legacy-confirmation','ee-direct'):raise ValueError('Explicit policy required')
    plan=expected_plan(mode,policy)
    if host.get('schema')!='bg-redux-book-host/1' or host.get('nonce')!=nonce or host.get('mode')!=mode or host.get('confirmation_policy')!=policy or host.get('completed')is not True or host.get('error') or host.get('os_pointer_input')is not False or host.get('direct_spell_mutation')is not False:raise ValueError('Incomplete/stale/forced native Erase host')
    if runtime.get('schema')!='bg-redux-book-runtime/1' or runtime.get('nonce')!=nonce or runtime.get('mode')!=mode or runtime.get('confirmation_policy')!=policy or runtime.get('planned')!=plan or runtime.get('steps')!=len(plan) or runtime.get('completed')is not True:raise ValueError('Erase plan coverage incomplete/stale')
    return plan

def intended_page(before,after,require_index=True):
    """One known entry, all same-page memorized copies; preserve order/flags/slots."""
    known=before['known']
    matches=[i for i,r in enumerate(known) if r['resref'].upper()==TARGET]
    if len(matches)!=1 or require_index and matches!=[2]:raise ValueError('Pinned intended known target/index absent')
    expected=copy.deepcopy(before)
    expected['known']=[r for r in known if r['resref'].upper()!=TARGET]
    expected['memorized']=[r for r in before['memorized'] if r['resref'].upper()!=TARGET]
    if expected!=after:raise ValueError('Erase changed wrong resref/order/flags/slots or left target copies')

def world_delta(before,after,erased):
    caster_surfaces(before);caster_surfaces(after)
    if not erased:return equal_except_selection(before,after)
    left=copy.deepcopy(before);right=copy.deepcopy(after)
    identities=[a['script_name'].casefold() for a in before['party']]
    if identities!=['none','imoen','jaheira','minsc'] or [a['script_name'].casefold() for a in after['party']]!=identities:
        raise ValueError('Four-party identity differs')
    identity=before['party'][1]['runtime_id']
    for group in ('party','current_area_actors'):
        aa=[r for r in left[group] if r['runtime_id']==identity];bb=[r for r in right[group] if r['runtime_id']==identity]
        if len(aa)!=1 or len(bb)!=1:raise ValueError('Caster missing/duplicate')
        a=page(aa[0],1,1);b=page(bb[0],1,1);intended_page(a,b)
        a['known']=[];b['known']=[];a['memorized']=[];b['memorized']=[]
    equal_except_selection(left,right)

def wire_delta_guard(before,after):
    left=copy.deepcopy(before);right=copy.deepcopy(after)
    if [r['name'] for r in left]!=['none','imoen','jaheira','minsc'] or [r['name'] for r in right]!=[r['name'] for r in left]:raise ValueError('Wire identity differs')
    aa=[p for p in left[1]['pages'] if p['type']==1 and p['level']==1]
    bb=[p for p in right[1]['pages'] if p['type']==1 and p['level']==1]
    if len(aa)!=1 or len(bb)!=1:raise ValueError('Wire target page absent/duplicate')
    # CREImporter writes known spells in reverse order; target identity is independent of that order.
    intended_page(aa[0],bb[0],require_index=False)
    aa[0]['known']=[];bb[0]['known']=[];aa[0]['memorized']=[];bb[0]['memorized']=[]
    if left!=right:raise ValueError('Other saved spellbook fields changed')

def target_binding(meta,event,names,controlled):
    matches=[(i,r) for i,r in enumerate(meta['shown']) if r['resref']==TARGET]
    if len(matches)!=1:raise ValueError('Missing/duplicate displayed intended spell')
    visible,row=matches[0]
    if row['original_index']!=2 or controlled and visible!=0:raise ValueError('Wrong original/displayed target index')
    if (event['pack'],event['window'],event['control'],event['actual_value'],event.get('action'),event['actual_tooltip'])!=('GUIMG',2,27+visible,2,'RightPress',names[TARGET]['name']):
        raise ValueError('Actual RightPress target binding differs')
    return visible!=2

def callback_inventory(events,rows,plan):
    requests=[r for r in rows if r['event']=='request'];dispatched=[e for e in events if e['step']>=0]
    expected={'mage.portrait':('PORTWIN',0,1),'mage.open':('OPTWIN',0,5),'mage.level':('GUIMG',2,62),
      'mage.erase':('GUIMG',3,6),'mage.erase-again':('GUIMG',3,6),'mage.cancel':('GUIMG',101,1),
      'mage.confirm':('GUIMG',101,0),'mage.close':('OPTWIN',0,5),'leader-portrait':('PORTWIN',0,0)}
    if len(requests)!=len(dispatched):raise ValueError('Missing/extra dispatched callbacks')
    for r,e in zip(requests,dispatched):
        if r['step']!=e['step'] or [r[k] for k in ('pack','window','control')]!=[e[k] for k in ('pack','window','control')]:raise ValueError('Request/dispatch identity mismatch')
        name=plan[e['step']]
        if name!='mage.info' and (e['pack'],e['window'],e['control'])!=expected[name]:raise ValueError('Wrong ordinary callback route')
        if e.get('action')!=('RightPress' if name=='mage.info' else 'Press'):raise ValueError('Wrong registered action kind')
    return requests
