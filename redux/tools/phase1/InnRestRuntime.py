"""External ordinary inn rest plan; no setup setters or production callbacks."""
import json
from pathlib import Path
import GemRB

PACKS=('PORTWIN','OPTWIN','GUISTORE','GUIOPT','GUISAVE')
OUTPUT=None
NONCE=MODE=POLICY=None
PLAN=[]
ROWS=[]
INDEX=CAPTURE=0

def view(pack,window):
    found=GemRB.GetView(pack,window)
    return found if found and found.IsVisible()else None

def control(pack,window,identifier):
    parent=view(pack,window);found=parent.GetControl(identifier)if parent else None
    if not found or not found.IsVisible()or found.Flags&(1<<29):raise RuntimeError('Inn rest control absent or disabled')
    return found

def press(pack,window,identifier):
    found=control(pack,window,identifier)
    GemRB.SetVar('RDXBookPressPack',PACKS.index(pack)+1);GemRB.SetVar('RDXBookPressWindow',window);GemRB.SetVar('RDXBookPressControl',identifier)
    ROWS.append(dict(event='request',step=INDEX,pack=pack,window=window,control=identifier,value=found.Value))

def command(number):
    if number not in(3,4,5):raise RuntimeError('Inn rest plan cannot invoke debug setup commands')
    GemRB.SetVar('RDXInnCommand',number);ROWS.append(dict(event='command-request',step=INDEX,command=number))

def observe(name,gold=100,store=False,confirmation=False,option=None):
    global CAPTURE
    if GemRB.GetCurrentArea().upper()!='AR0704'or GemRB.GetPartySize()!=4:raise RuntimeError('Measured four-party inn input required')
    option=int(POLICY=='on')if option is None else option
    actual=dict(gold=GemRB.GameGetPartyGold(),option=GemRB.GetVar('Over Confirm Everything'),error=bool(view('GUISTORE',10)),confirmation=bool(view('GUISTORE',11)),store=bool(view('GUISTORE',7)))
    expected=dict(gold=gold,option=option,error=False,confirmation=confirmation,store=store)
    if actual!=expected:
        with (OUTPUT/'unexpected-observations.jsonl').open('a',encoding='utf8')as log:log.write(json.dumps(dict(nonce=NONCE,mode=MODE,name=name,step=INDEX,actual=actual,expected=expected))+'\n')
        raise RuntimeError('Unexpected inn rest gold/option/modal boundary: '+repr(actual))
    data=GemRB.GetStore()if store else None
    if store and(not data or data['StoreType']!=2 or data['StoreName']!=33355 or data['StoreButtons'][0]!=6 or list(data['StoreRoomPrices'])!=[1,6,10,16]):raise RuntimeError('Wrong stock inn/type/rooms/prices')
    if confirmation and control('GUISTORE',11,3).QueryText()!=GemRB.GetString(15358):raise RuntimeError('Wrong actual rest prompt')
    row=dict(schema='bg-redux-inn-rest-observation/1',nonce=NONCE,mode=MODE,policy=POLICY,name=name,step=INDEX,**actual,
        store_details=data,room=GemRB.GetVar('RentIndex'),draft=GemRB.GetVar('BG2EE Confirmation Draft'),game_time=GemRB.GetGameTime())
    CAPTURE+=1;row['capture']=CAPTURE
    (OUTPUT/('capture-%d.inn.json'%CAPTURE)).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
    GemRB.SetVar('RDXBookCapture',CAPTURE);ROWS.append(dict(event='observe',step=INDEX,name=name,capture=CAPTURE))

def Configure(output,nonce,mode,policy):
    global OUTPUT,NONCE,MODE,POLICY,PLAN,ROWS,INDEX,CAPTURE
    if mode not in('off','on','reload')or policy not in('off','on')or mode!='reload'and mode!=policy or len(nonce)!=32 or any(c not in'0123456789abcdef'for c in nonce):raise RuntimeError('Explicit inn rest mode/policy/nonce required')
    OUTPUT=Path(output);NONCE=nonce;MODE=mode;POLICY=policy;PLAN=[];ROWS=[];INDEX=CAPTURE=0
    def add(name,fn):PLAN.append((name,fn))
    if mode=='reload':add('reloaded-rest-save',lambda:observe('reloaded-rest-save',99))
    else:
        add('loaded-inn',lambda:observe('loaded-inn',option=0))
        if mode=='on':
            for name,pack,window,identifier in(('settings.open','OPTWIN',0,7),('settings.gameplay','GUIOPT',2,9),('settings.feedback','GUIOPT',8,5)):
                add(name,lambda p=pack,w=window,c=identifier:press(p,w,c))
            add('settings.before-toggle',lambda:observe('settings.before-toggle',option=0))
            add('settings.toggle',lambda:press('GUIOPT',9,41))
            add('settings.draft',lambda:observe('settings.draft',option=0))
            add('settings.done',lambda:press('GUIOPT',9,26))
            add('settings.committed',lambda:observe('settings.committed'))
            add('settings.gameplay-done',lambda:press('GUIOPT',8,7))
            add('settings.return',lambda:press('GUIOPT',2,11))
        add('talk',lambda:command(3));add('response',lambda:command(4));add('dialogue-end',lambda:command(5))
        add('inn-room-page',lambda:observe('inn-room-page',store=True))
        add('room-zero',lambda:press('GUISTORE',7,0))
        add('room-selected',lambda:observe('room-selected',store=True))
        add('rent',lambda:press('GUISTORE',7,11))
        if mode=='on':
            add('confirmation',lambda:observe('confirmation',store=True,confirmation=True))
            add('cancel',lambda:press('GUISTORE',11,1))
            add('after-cancel',lambda:observe('after-cancel',store=True))
            add('rent-again',lambda:press('GUISTORE',7,11))
            add('confirmation-again',lambda:observe('confirmation-again',store=True,confirmation=True))
            add('confirm',lambda:press('GUISTORE',11,0))
        add('after-rest',lambda:observe('after-rest',99,store=True))
        add('store-done',lambda:press('GUISTORE',3,0))
        add('closed',lambda:observe('closed',99))
    for name in('RDXBookComplete','RDXBookPressPack','RDXBookCapture','RDXInnCommand'):GemRB.SetVar(name,0)

def Step():
    global INDEX
    for name in('RDXBookPressPack','RDXBookCapture','RDXInnCommand'):GemRB.SetVar(name,0)
    if INDEX>=len(PLAN):GemRB.SetVar('RDXBookComplete',1)
    else:
        _,fn=PLAN[INDEX];GemRB.SetVar('RDXBookStep',INDEX);fn();INDEX+=1
    row=dict(schema='bg-redux-inn-rest-runtime/1',nonce=NONCE,mode=MODE,policy=POLICY,planned=[name for name,_ in PLAN],steps=INDEX,completed=INDEX==len(PLAN),rows=ROWS,debug_setup_invoked=False,physical_pointer_input=False,original_parity=None)
    (OUTPUT/'book-runtime.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8')
