import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hotkey_harness_test', HERE/'hotkey_harness.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class HotkeyJourneyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.profile = self.directory/'profile'
        self.profile.mkdir()
        self.base = dict(inventory='i', character_record='r', journal='j')
        self.swap = dict(inventory='r', character_record='i', journal='j')
        self.pin = dict(mode='hotkeys-edit', nonce='fresh-edit', profile=str(self.profile.resolve()))
        self.capture_number = 0
        self.make_stage()

    def tearDown(self): self.temp.cleanup()

    def write(self, name, data):
        (self.directory/name).write_text(json.dumps(data), encoding='utf-8')

    def capture(self, pack=None):
        self.capture_number += 1
        n = self.capture_number
        bmp = bytearray(58)
        bmp[:2] = b'BM'
        struct.pack_into('<I',bmp,2,len(bmp))
        struct.pack_into('<ii',bmp,18,1024,768)
        (self.directory/('capture-%d.bmp'%n)).write_bytes(bmp)
        self.write('capture-%d.ui.json'%n, dict(controls=[dict(pack=pack,window=2,visible=True)] if pack else []))
        for suffix in ('state','observer'): self.write('capture-%d.%s.json'%(n,suffix), {})
        return n

    def profile_state(self, persisted):
        data = tool.ini_bytes(persisted) if persisted is not None else None
        return dict(path=str((self.profile/'gemrb-keymap.ini').resolve()), exists=data is not None,
                    bytes_hex=data.hex() if data else None, sha256=hashlib.sha256(data).hexdigest() if data else None)

    def make_stage(self, reload=False):
        partial = dict(self.base,inventory='r',character_record='')
        contracts = [('initial',self.swap if reload else self.base,None,self.swap if reload else None),
                     ('final',self.swap,None,self.swap), ('mouse-inventory',self.swap,None,self.swap)]
        if reload:
            contracts += [('reload-editor',self.swap,self.swap,self.swap)]
        else:
            contracts += [('conflict-rejected',self.base,self.base,None),('replace-staged',self.base,partial,None),
                ('cancelled',self.base,None,None),('clear-staged',self.base,dict(self.base,inventory=''),None),
                ('clear-cancelled',self.base,None,None),('swap-staged',self.base,self.swap,None),
                ('applied',self.swap,None,self.swap),('defaults-staged',self.swap,self.base,self.swap),
                ('defaults-cancelled',self.swap,None,self.swap),('defaults-applied',self.base,None,self.base),
                ('final-applied',self.swap,None,self.swap)]
        states=[]
        for name,live,staged,persisted in contracts:
            label='Inventory : '+(staged['inventory'].upper() or 'Unbound') if staged else None
            states.append(dict(name=name,nonce=self.pin['nonce'],bindings=live,staged=staged,editor_open=staged is not None,
                selected='inventory' if staged else None, selected_label='Inventory' if staged else None,
                visible_rows=[label] if label else [], status='R is assigned to Character Record. Replace explicitly.',
                profile=self.profile_state(persisted),step=200 if name=='mouse-inventory' else 1,
                capture=self.capture('GUIINV' if name=='mouse-inventory' else None)))
        actions={'reload.cancel':14} if reload else {'conflict.assign':6001,'conflict.replace':6003,'cancel.callback':14,
            'clear.callback':6002,'clear.cancel':14,'apply.replace':6003,'apply.assign':6001,'apply.callback':11,
            'defaults-cancel.callback':6004,'defaults-cancel.cancel':14,'defaults-apply.defaults':6004,
            'defaults-apply.apply':11,'final.replace':6003,'final.assign':6001,'final.apply':11}
        callbacks=[]
        for action,cid in actions.items():
            callbacks.append(dict(action=action,sequence=len(callbacks)+1,pack='WIN_KEYS',window=0,control=cid,nonce=self.pin['nonce']))
        callbacks.append(dict(action='inventory.mouse-callback',sequence=len(callbacks)+1,step=199,pack='OPTWIN',window=0,control=3,nonce=self.pin['nonce']))
        for row in callbacks:
            self.write('callback-%d.json'%row['sequence'],dict(row,schema='bg-redux-callback-dispatch/1',performed=True))
        keys=[]
        for prefix,mapping in ([('reloaded',self.swap)] if reload else [('original',self.base),('swapped',self.swap),('restored',self.base),('final',self.swap)]):
            for action,pack in (('inventory','GUIINV'),('character_record','GUIREC'),('journal','GUIJRNL')):
                n=len(keys)+1
                row=dict(sequence=n,key=mapping[action],nonce=self.pin['nonce'],step=n*2,observed_step=n*2+1,
                         observation=prefix+'.'+action,capture=self.capture(pack),bindings_before=mapping,bindings_after=mapping,
                         profile_before=self.profile_state(None if prefix=='original' else mapping),
                         profile_after=self.profile_state(None if prefix=='original' else mapping))
                keys.append(row)
                self.write('key-%d.json'%n,dict(schema='bg-redux-key-dispatch/1',sequence=n,nonce=self.pin['nonce'],
                    keycode=ord(mapping[action]),modifiers=0,keydown_dispatched=True,keyup_dispatched=True,
                    route='EventMgr::DispatchEvent',os_input_injected=False))
                self.write('key-%d-before.ui.json'%n,dict(controls=[]))
                for phase in ('before','after'):
                    for suffix in ('state','observer'):
                        self.write('key-%d-%s.%s.json'%(n,phase,suffix),dict(ammo=40,action=None))
        self.runtime=dict(schema='bg-redux-hotkey-runtime/1',mode=self.pin['mode'],nonce=self.pin['nonce'],
            completed=True,steps=100,planned_steps=100,process=dict(pid=123,startup_nonce='process-edit'),
            baseline=self.base,defaults=self.base,expected_swapped=self.swap,states=states,callbacks=callbacks,keys=keys)
        self.host=dict(completed=True,nonce=self.pin['nonce'],journey=self.pin['mode'],callbacks=len(callbacks),native_keys=len(keys))
        for suffix in ('state','observer'):
            for stage in ('before','after'): self.write(stage+'.'+suffix+'.json',dict(ammo=40,effects=[1],action=None))
        (self.profile/'gemrb-keymap.ini').write_bytes(tool.ini_bytes(self.swap))
        self.save()

    def save(self):
        self.write('hotkey-runtime.json',self.runtime)
        self.write('menu-host-result.json',self.host)

    def state(self,name): return next(s for s in self.runtime['states'] if s['name']==name)

    def test_complete_callback_and_eventmgr_evidence_preserves_claim_limits(self):
        result=tool.validate_stage(self.directory,self.pin)
        self.assertEqual(result['eventmgr_key_pairs'],12)
        self.assertFalse(result['pointer_hit_testing'])
        self.assertFalse(result['hidden_rng_identity_proven'])

    def test_cancel_cannot_apply_or_create_profile(self):
        self.state('cancelled')['bindings']=self.swap
        self.save()
        with self.assertRaisesRegex(ValueError,'Native/staged'): tool.validate_stage(self.directory,self.pin)
        self.state('cancelled')['bindings']=self.base
        self.state('cancelled')['profile']=self.profile_state(self.swap)
        self.save()
        with self.assertRaisesRegex(ValueError,'Persistence or cancel'): tool.validate_stage(self.directory,self.pin)

    def test_implicit_conflict_replacement_or_inert_defaults_fail(self):
        self.state('conflict-rejected')['staged']=self.swap
        self.save()
        with self.assertRaisesRegex(ValueError,'Native/staged'): tool.validate_stage(self.directory,self.pin)
        self.state('conflict-rejected')['staged']=self.base
        self.state('defaults-staged')['staged']=self.swap
        self.save()
        with self.assertRaisesRegex(ValueError,'Native/staged'): tool.validate_stage(self.directory,self.pin)

    def test_live_map_success_does_not_hide_missing_saved_bindings(self):
        self.state('applied')['profile']=self.profile_state(None)
        self.save()
        with self.assertRaisesRegex(ValueError,'Persistence'): tool.validate_stage(self.directory,self.pin)

    def test_staged_model_without_actual_visible_row_is_rejected(self):
        self.state('replace-staged')['visible_rows']=['Inventory : I']
        self.save()
        with self.assertRaisesRegex(ValueError,'visible staged row'): tool.validate_stage(self.directory,self.pin)

    def test_callback_target_and_nonce_are_native_pinned(self):
        path='callback-1.json'
        row=json.loads((self.directory/path).read_text())
        row['control']=6003
        self.write(path,row)
        with self.assertRaisesRegex(ValueError,'target/nonce'): tool.validate_stage(self.directory,self.pin)
        row['control']=6001; row['nonce']='stale'
        self.write(path,row)
        with self.assertRaisesRegex(ValueError,'target/nonce'): tool.validate_stage(self.directory,self.pin)

    def test_resolvekey_lookup_or_missing_keyup_cannot_claim_eventmgr_dispatch(self):
        row=json.loads((self.directory/'key-1.json').read_text())
        row['route']='KeyMap::ResolveKey'
        self.write('key-1.json',row)
        with self.assertRaisesRegex(ValueError,'EventMgr'): tool.validate_stage(self.directory,self.pin)
        row['route']='EventMgr::DispatchEvent'; row['keyup_dispatched']=False
        self.write('key-1.json',row)
        with self.assertRaisesRegex(ValueError,'EventMgr'): tool.validate_stage(self.directory,self.pin)

    def test_key_must_open_new_correct_window_after_render_boundary(self):
        row=self.runtime['keys'][0]
        self.write('capture-%d.ui.json'%row['capture'],dict(controls=[dict(pack='GUIREC',window=2,visible=True)]))
        with self.assertRaisesRegex(ValueError,'wrong/missing'): tool.validate_stage(self.directory,self.pin)
        self.write('capture-%d.ui.json'%row['capture'],dict(controls=[dict(pack='GUIINV',window=2,visible=True)]))
        row['observed_step']=row['step']
        self.save()
        with self.assertRaisesRegex(ValueError,'boundary'): tool.validate_stage(self.directory,self.pin)

    def test_truncated_capture_and_changed_world_are_not_passes(self):
        number=self.state('initial')['capture']
        data=(self.directory/('capture-%d.bmp'%number)).read_bytes()
        (self.directory/('capture-%d.bmp'%number)).write_bytes(b'BM')
        with self.assertRaisesRegex(ValueError,'screenshot'): tool.validate_stage(self.directory,self.pin)
        (self.directory/('capture-%d.bmp'%number)).write_bytes(data)
        self.write('after.state.json',dict(ammo=39,effects=[1],action=None))
        with self.assertRaisesRegex(ValueError,'state changed'): tool.validate_stage(self.directory,self.pin)

    def test_reload_requires_exact_saved_pin_and_native_loaded_map(self):
        self.pin.update(mode='hotkeys-reload',nonce='fresh-reload',baseline=self.base,expected_bindings=self.swap,
                        profile_sha256=hashlib.sha256(tool.ini_bytes(self.swap)).hexdigest())
        self.make_stage(reload=True)
        self.assertEqual(tool.validate_stage(self.directory,self.pin)['eventmgr_key_pairs'],3)
        self.state('initial')['bindings']=self.base
        self.save()
        with self.assertRaisesRegex(ValueError,'Native/staged'): tool.validate_stage(self.directory,self.pin)

    def test_two_process_validation_rejects_profile_or_process_reuse(self):
        first=dict(mode='hotkeys-edit',pin=dict(profile='A',nonce='a'),process=dict(owned_pid=123),
            validation=dict(process=dict(pid=123,startup_nonce='one'),profile_sha256='hash',baseline=self.base,persisted_bindings=self.swap))
        second=copy.deepcopy(first)
        second.update(mode='hotkeys-reload',pin=dict(profile='B',nonce='b',profile_sha256='hash'),process=dict(owned_pid=456))
        second['validation']['process']=dict(pid=456,startup_nonce='two')
        self.assertTrue(tool.validate_pair([first,second])['exact_saved_profile_reloaded'])
        second['pin']['profile']='A'
        with self.assertRaisesRegex(ValueError,'not fresh'): tool.validate_pair([first,second])
        second['pin']['profile']='B'; second['validation']['process']['pid']=123
        with self.assertRaisesRegex(ValueError,'another process'): tool.validate_pair([first,second])


class JourneyControlRoutingTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.editor=types.SimpleNamespace(Editor=object(),Names=['action_%02d'%i for i in range(13)]+['inventory'],
                                          Page=0,Selected=0,ROWS=12)
        self.menu=types.ModuleType('MenuRuntime')
        self.menu.PLAN=[('select-inventory',None,False)]
        self.menu.INDEX=0
        self.menu.press=lambda *args:self.calls.append(args)
        self.menu.control=lambda *args:types.SimpleNamespace(SetText=lambda text:self.calls.append(args+(text,)))
        gem=types.SimpleNamespace(GetVar=lambda name:0)
        self.modules=patch.dict(sys.modules,dict(MenuRuntime=self.menu,GUIHotkeys=self.editor,GemRB=gem,
                                                GUIDefines=types.SimpleNamespace(SV_SAVEPATH=1)))
        self.modules.start()
        spec=importlib.util.spec_from_file_location('hotkey_runtime_test',HERE/'gui/HotkeyRuntime.py')
        self.runtime=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runtime)
        self.runtime.NONCE='fresh'

    def tearDown(self): self.modules.stop()

    def test_selection_uses_registered_page_and_row_callbacks_without_mutating_editor(self):
        self.runtime.select('inventory')
        self.assertEqual(self.calls,[('WIN_KEYS',0,6006)])
        self.assertEqual(self.editor.Page,0)
        self.assertEqual(self.editor.Selected,0)
        self.assertEqual(len(self.menu.PLAN),2)
        self.editor.Page=1  # Simulate completion of the requested native page callback.
        self.runtime.select('inventory')
        self.assertEqual(self.calls[-1],('WIN_KEYS',0,5001))
        self.assertEqual(self.editor.Selected,0)

    def test_editable_input_requires_actual_selected_row(self):
        with self.assertRaisesRegex(RuntimeError,'selected editor action'):
            self.runtime.text('inventory','r')
        self.assertEqual(self.calls,[])
        self.editor.Selected=13
        self.runtime.text('inventory','r')
        self.assertEqual(self.calls,[('WIN_KEYS',0,6000,'r')])


if __name__=='__main__': unittest.main()
