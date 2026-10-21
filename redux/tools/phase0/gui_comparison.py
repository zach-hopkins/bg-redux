"""Explicit legacy representation diagnostic; raw comparisons remain primary.

Applies only the source-verified GAMEV2/CRE contracts observed in these runs.
This is not an original-executable oracle or a complete save-format proof.
"""
from save_harness import normalize, differences

def fold_variables(variables):
    folded={}
    for name,value in variables.items():
        key=name.upper()
        if key in folded and folded[key]!=value:
            raise ValueError('Conflicting case-insensitive variables')
        folded[key]=value
    return folded

def legacy_view(state, before_save=False):
    state=normalize(state)
    applied=[]
    if before_save:
        original=state['game_time']
        state['game_time']=original//15*15
        if original!=state['game_time']:
            applied.append(dict(contract='GAME seconds precision',before=original,after=state['game_time']))
    state['globals']=fold_variables(state['globals'])
    if state['area_locals'] is not None: state['area_locals']=fold_variables(state['area_locals'])
    for group in ['party','stored_npcs','current_area_actors']:
        for actor in state[group]:
            actor['locals']=fold_variables(actor['locals'])
            effects=[]
            for effect in actor['effects']:
                # The snapshot's first resource string spans the overlaid
                # VariableName storage for these marker records. Require the
                # collected locals to independently contain the same name/value.
                name=effect['resources'][0].upper()
                if (effect['opcode']==187 and effect['special']==1 and effect['timing']==11
                    and name in actor['locals'] and actor['locals'][name]==effect['parameters'][0]):
                    applied.append(dict(contract='CRE variable marker',group=group,actor=actor['script_name'],
                                        name=name,value=actor['locals'][name]))
                else: effects.append(effect)
            actor['effects']=effects
    return state,applied

def compare(before,after):
    a,applied_before=legacy_view(before,True)
    b,applied_after=legacy_view(after)
    diff=differences(a,b)
    return dict(schema='bg-redux-legacy-semantic-diagnostic/1',passed=not diff,differences=len(diff),
        applied_before=applied_before,applied_after=applied_after,
        contracts=['GAMEV2 writes GameTime/15 and reads seconds*15; only pre-save time is quantized.',
                   'Variable names use the engine case-insensitive map; values remain compared.',
                   'Opcode187/special1/timing11 marker records represented by equal collected actor locals; other effects/order remain compared.'],
        scope='Collected initialized state only; not complete SAV content, original-runtime equivalence or visual correctness.'),diff
