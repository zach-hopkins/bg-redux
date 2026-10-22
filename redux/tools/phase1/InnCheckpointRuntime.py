"""Declared debug setup and ordinary inn callbacks. External diagnostic only."""
import json
from pathlib import Path
import GemRB
PACKS=('PORTWIN','OPTWIN','GUISTORE','GUIOPT','GUISAVE')
OUTPUT=None
NONCE=None
MODE=None
PLAN=[]
ROWS=[]
INDEX=CAPTURE=0

def view(pack,window):
    result=GemRB.GetView(pack,window)
    return result if result and result.IsVisible()else None
def control(pack,window,cid):
    window=view(pack,window);result=window.GetControl(cid)if window else None
    if not result or not result.IsVisible():raise RuntimeError('Actual inn control absent')
    if result.Flags&(1<<29):raise RuntimeError('Disabled actual inn control cannot be forced')
    return result
def press(pack,window,cid):
    actual=control(pack,window,cid)
    GemRB.SetVar('RDXBookPressPack',PACKS.index(pack)+1);GemRB.SetVar('RDXBookPressWindow',window);GemRB.SetVar('RDXBookPressControl',cid)
    ROWS.append(dict(event='request',step=INDEX,pack=pack,window=window,control=cid,value=actual.Value))
def command(number):
    GemRB.SetVar('RDXInnCommand',number)
    ROWS.append(dict(event='command-request',step=INDEX,command=number))
def observe(name,store=False,error=False,confirmation=False):
    global CAPTURE
    if GemRB.GetCurrentArea().upper()!='AR0704'or GemRB.GetPartySize()!=4:raise RuntimeError('Declared inn fixture area/party absent')
    row=dict(schema='bg-redux-inn-observation/1',nonce=NONCE,mode=MODE,name=name,step=INDEX,
        area=GemRB.GetCurrentArea(),gold=GemRB.GameGetPartyGold(),option=GemRB.GetVar('Over Confirm Everything'),
        error=bool(view('GUISTORE',10)),confirmation=bool(view('GUISTORE',11)),store=None)
    if row['error']!=error or row['confirmation']!=confirmation:raise RuntimeError('Unexpected actual inn modal boundary')
    if store:
        data=GemRB.GetStore()
        if not data or data['StoreType']!=2 or data['StoreName']!=33355 or data['StoreButtons'][0]!=6 or list(data['StoreRoomPrices'])!=[1,6,10,16]:raise RuntimeError('Wrong actual stock inn/type/rooms/prices')
        control('GUISTORE',7,11);row.update(store=data,room=GemRB.GetVar('RentIndex'))
    if error and control('GUISTORE',10,3).QueryText()!=GemRB.GetString(11051):raise RuntimeError('Actual insufficient-gold message differs')
    if confirmation and control('GUISTORE',11,3).QueryText()!=GemRB.GetString(15358):raise RuntimeError('Actual inn confirmation text differs')
    CAPTURE+=1;GemRB.SetVar('RDXBookCapture',CAPTURE);row['capture']=CAPTURE
    (OUTPUT/('capture-%d.inn.json'%CAPTURE)).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
    ROWS.append(dict(event='observe',name=name,step=INDEX,capture=CAPTURE))

def Configure(output,nonce,mode,policy):
    global OUTPUT,NONCE,MODE,PLAN,ROWS,INDEX,CAPTURE
    if mode not in ('prepare','observe')or policy!='characterize-current'or len(nonce)!=32 or any(c not in'0123456789abcdef'for c in nonce):raise RuntimeError('Explicit inn diagnostic scope/nonce required')
    OUTPUT=Path(output);NONCE=nonce;MODE=mode;PLAN=[];ROWS=[];INDEX=CAPTURE=0
    def add(name,fn):PLAN.append((name,fn))
    if mode=='prepare':
        add('debug-transfer',lambda:command(1))
        add('transferred-zero-gold',lambda:observe('transferred-zero-gold'))
    else:add('reloaded-checkpoint',lambda:observe('reloaded-checkpoint'))
    add('talk',lambda:command(3));add('response',lambda:command(4));add('dialogue-end',lambda:command(5))
    add('inn-room-page',lambda:observe('inn-room-page',True))
    add('room-zero',lambda:press('GUISTORE',7,0))
    add('room-selected',lambda:observe('room-selected',True))
    add('rent',lambda:press('GUISTORE',7,11))
    if mode=='prepare':
        add('zero-gold-error',lambda:observe('zero-gold-error',True,True))
        add('error-done',lambda:press('GUISTORE',10,0))
        add('after-error',lambda:observe('after-error',True))
    else:
        add('current-forced-confirmation',lambda:observe('current-forced-confirmation',True,False,True))
        add('cancel',lambda:press('GUISTORE',11,1))
        add('after-cancel',lambda:observe('after-cancel',True))
    add('store-done',lambda:press('GUISTORE',3,0))
    add('closed',lambda:observe('closed'))
    if mode=='prepare':
        add('debug-add-100',lambda:command(2))
        add('checkpoint',lambda:observe('checkpoint'))
    GemRB.SetVar('RDXBookComplete',0);GemRB.SetVar('RDXBookPressPack',0);GemRB.SetVar('RDXBookCapture',0);GemRB.SetVar('RDXInnCommand',0)

def Step():
    global INDEX
    GemRB.SetVar('RDXBookPressPack',0);GemRB.SetVar('RDXBookCapture',0);GemRB.SetVar('RDXInnCommand',0)
    if INDEX>=len(PLAN):GemRB.SetVar('RDXBookComplete',1)
    else:
        _,fn=PLAN[INDEX];GemRB.SetVar('RDXBookStep',INDEX);fn();INDEX+=1
    row=dict(schema='bg-redux-inn-runtime/1',nonce=NONCE,mode=MODE,planned=[name for name,_ in PLAN],steps=INDEX,completed=INDEX==len(PLAN),rows=ROWS,
        ordinary_campaign_transfer=False,debug_setup_declared=True,original_parity=None,physical_pointer_input=False)
    (OUTPUT/'book-runtime.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
