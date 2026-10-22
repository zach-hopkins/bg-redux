"""Independent ordinary information-page/native-control contract, version 1."""
from pathlib import Path
SCHEMA='bg-redux-known-information-page/1'
ROWS=7
NAME=0x7fff0400
UP,DOWN,COUNT,ACTION,TEXT,INFO_UP,INFO_DOWN=range(0x7fff0410,0x7fff0417)

def validate_page(layout,shown,controls,pack,actor,kind,level,*,expected_module=None,expected_help=None,require_unselected=True):
    if not isinstance(layout,dict)or layout.get('schema')!=SCHEMA:raise ValueError('Missing/unknown spellbook information layout version')
    if (layout.get('pack'),layout.get('actor'),layout.get('kind'),layout.get('level'),layout.get('page_size'))!=(pack,actor,kind,level,ROWS):raise ValueError('Information page context/row pool differs')
    if layout.get('per_label_style_observed')is not False or layout.get('all_pages_visited')is not False:raise ValueError('Single-page observation inflated style/navigation scope')
    if expected_module is not None and Path(layout['module']).resolve()!=Path(expected_module).resolve():raise ValueError('Wrong production information helper provider')
    top=layout.get('top');total=len(shown);last=max(0,((total-1)//ROWS)*ROWS)
    if type(top)is not int or top<0 or top>last or top%ROWS:raise ValueError('Invalid actual page offset')
    visible=shown[top:top+ROWS]
    if layout.get('visible_rows')!=visible:raise ValueError('Visible page differs from full independent sorted known list')
    def field(cid,visible=True):
        rows=[r for r in controls if r.get('pack')==pack and r.get('window')==2 and r.get('id')==cid]
        if len(rows)!=1 or bool(rows[0].get('visible'))!=visible:raise ValueError('Missing/duplicate/wrong-visibility spellbook control: '+str(cid))
        return rows[0]
    for i in range(24):
        icon=field(27+i,i<len(visible))
        if i>=ROWS:continue
        name=field(NAME+i,i<len(visible))
        if i<len(visible):
            expected=visible[i]
            if (icon.get('value'),icon.get('tooltip'),icon.get('stored_tooltip'),icon.get('picture_present'))!=(expected['original_index'],expected['name'],expected['name'],True)or icon.get('disabled'):raise ValueError('Actual visible icon identity/picture differs')
            size=icon.get('picture_size');rect=icon.get('rect')
            if not icon.get('flags',0)&2 or icon.get('picture_observable')is not True or not isinstance(size,list)or len(size)!=2 or any(type(n)is not int or n<=0 for n in size)or not isinstance(rect,list)or len(rect)!=4 or min(rect[2:])<=0:raise ValueError('Actual visible icon geometry/picture metadata absent')
            if (name.get('value'),name.get('text'),name.get('tooltip'))!=(expected['original_index'],expected['name'],expected['name'])or name.get('disabled'):raise ValueError('Persistent known name/original index differs')
    text='%d/%d (%d-%d/%d)'%(top//ROWS+1,max(1,(total+ROWS-1)//ROWS),top+1 if total else 0,min(total,top+ROWS),total)
    if layout.get('page_text')!=text or field(COUNT).get('text')!=text:raise ValueError('Page/range/total label differs')
    if field(UP).get('disabled')!=(top==0)or field(DOWN).get('disabled')!=(top+ROWS>=total):raise ValueError('Actual page navigation bounds differ')
    selected=layout.get('selected')
    if require_unselected and selected is not None:raise ValueError('Existing journey unexpectedly selected information row')
    if selected is not None and selected not in visible:raise ValueError('Selected identity outside actual visible page')
    help_text=layout.get('resolved_help')
    if layout.get('default_help_strref')!=39254 or not isinstance(help_text,str)or not help_text:raise ValueError('Full localized default help binding absent')
    if expected_help is not None and help_text!=expected_help:raise ValueError('Default help differs from frozen configured TLK')
    expected_text=help_text if selected is None else selected['name']+'\n\n'+layout['selected_description']
    if layout.get('information_text')!=expected_text or field(TEXT).get('text')!=expected_text:raise ValueError('Actual full help/selected-description text differs')
    if selected is None and (layout.get('selected_description_ref')is not None or layout.get('selected_description')is not None):raise ValueError('Unselected page retained description metadata')
    action=field(ACTION)
    if layout.get('action_strref')!=(17189 if pack=='GUIMG'else 17224)or layout.get('resolved_action_label')!=layout.get('action_text'):raise ValueError('Separate action localization binding differs')
    if action.get('text')!=layout.get('action_text')or not isinstance(layout.get('action_text'),str)or not layout['action_text']or action.get('value')!=layout.get('action_value')or action.get('disabled')!=layout.get('action_disabled'):raise ValueError('Actual separate action text/value/state differs')
    if selected is None and (action.get('disabled')is not True or action.get('value')!=0):raise ValueError('Unselected page permits separate Memorize')
    if selected is not None and action.get('value')!=selected['original_index']:raise ValueError('Selected action targets wrong original index')
    for cid in (INFO_UP,INFO_DOWN):
        if field(cid).get('disabled'):raise ValueError('Information scrolling controls unavailable')
    return dict(layout=SCHEMA,visible_entries=len(visible),total_known=total,top=top,all_pages_visited=False,selected=selected,per_label_style_observed=False)
