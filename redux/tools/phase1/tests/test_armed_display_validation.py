"""Raw evidence controls for armed API parity and ordinary sheet refreshes."""
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
import test_weapon_query_validation as fixture
import armed_display_validation as validation

NONCE='0123456789abcdef0123456789abcdef'


class ArmedDisplayValidationTests(unittest.TestCase):
    def write(self,name,value):
        (self.path/name).write_text(json.dumps(value),encoding='utf8')

    def read(self,name):
        return json.loads((self.path/name).read_text(encoding='utf8'))

    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.path=Path(temp.name)
        row,metadata,state,cache=fixture.setup_case()
        self.bundle=json.loads(json.dumps(dict(row=row,item_metadata=metadata)))
        for pc,actor in enumerate(state['party'],1):
            actor['name']='Actor%d'%pc;actor['base_stats'][7]=actor['modified_stats'][7]=14
        state['party'][1]['inventory']['items']=[]
        observer=dict(actors=[dict(party_index=pc,cached_thac0=14) for pc in (1,2)])
        samples=[]
        for pc in (1,2):
            for hand in (0,1):
                total=13 if pc==1 and hand else 14
                details=dict(Slot=(35 if hand==0 else 9) if pc==1 else 10,
                    Flags=(1 if hand==0 else 17) if pc==1 else 33,
                    Enchantment=hand if pc==1 else 0,ToHitStats=dict(Base=14,Total=total))
                samples.append(dict(actor=pc,hand=hand,actor_name='Actor%d'%pc,before=14,after=14,
                    dual=pc==1,item=('SW1H01' if hand==0 else 'SW1H02') if pc==1 else None,
                    details=details,repeat_equal=True))
        captures={0:1,3:2,5:3,7:4,11:5,13:6,15:7,19:8}
        checks=[dict(action='armed.'+name,step=i,capture=captures.get(i)) for i,name in enumerate(validation.ACTIONS)]
        checks.append(dict(name='armed.rng-control',passed=True,result=10))
        for phase in ('cold','refreshed'):
            checks.append(dict(name='armed.matrix.'+phase,passed=True,api_calls=128,repeats=32,samples=copy.deepcopy(samples)))
        legacy=[]
        for s in samples:
            value=dict(actor=s['actor'],hand=s['hand'],before=14,after=s['details']['ToHitStats']['Total'],details=s['details'])
            legacy.append(value)
        for name in ('legacy-default','legacy-false'):
            checks.append(dict(name='armed.'+name,passed=True,equals_display_result=True,samples=copy.deepcopy(legacy)))
        sheets=[]
        for pack,pc in [('GUIREC',1),('GUIREC',2),('GUIINV',2),('GUIINV',1)]:
            details=[s['details'] for s in samples if s['actor']==pc]
            if pc==2:details=details[:1]
            sheet=dict(name='armed.sheet',passed=True,pack=pack,actor=pc,actor_name='Actor%d'%pc,
                panels=['Panel%d'%i for i in range(4)],headline='/'.join(str(d['ToHitStats']['Total']) for d in details),details=details)
            sheets.append(sheet)
        checks+=sheets
        self.write('armed-input.json',self.bundle)
        self.write('menu-runtime.json',dict(nonce=NONCE,steps=20,planned_steps=20,checks=checks))
        self.write('menu-host-result.json',dict(nonce=NONCE,completed=True,journey='display-armed',captures=8,callbacks=3,
            style_thac0_flag_loaded=True,style_thac0_flag_effective=True,legacy_style_control=False))
        self.write('before.state.json',state);self.write('before.observer.json',observer);self.write('before.weapons.json',cache)
        (self.path/'process.log').write_text('normal native output\n',encoding='utf8')
        final=copy.deepcopy(state);final['party'][0]['modified_stats'][7]=13
        self.write('after.state.json',final)
        final_observer=copy.deepcopy(observer);final_observer['actors'][0]['cached_thac0']=13
        self.write('after.observer.json',final_observer)
        for number in range(1,9):
            captured=copy.deepcopy(final if number==8 else state)
            captured['selection']=2 if number in (4,5) else 1
            self.write('capture-%d.state.json'%number,captured);self.write('capture-%d.observer.json'%number,observer)
            controls=[]
            if number in (3,4,5,6):
                s=sheets[number-3];pack=s['pack'];ids=(53,54,55,56) if pack=='GUIREC' else (77,78,79,80)
                values=list(zip(ids,s['panels']))+[(0x10000040 if pack=='GUIREC' else 0x10000055,s['headline']),
                    (0x1000000e if pack=='GUIREC' else 0x10000032,s['actor_name'])]
                controls=[dict(pack=pack,window=2,id=cid,visible=True,text=text) for cid,text in values]
            self.write('capture-%d.ui.json'%number,dict(controls=controls))
            bmp=bytearray(55);bmp[:2]=b'BM';struct.pack_into('<I',bmp,2,len(bmp));struct.pack_into('<ii',bmp,18,1,1)
            (self.path/('capture-%d.bmp'%number)).write_bytes(bmp)
        for n,step,cid in ((1,7,1),(2,11,1),(3,13,0)):
            self.write('callback-%d.json'%n,dict(sequence=n,runtime_step=step,nonce=NONCE,performed=True,pack='PORTWIN',window=0,control=cid))
            for side in ('before','after'):
                self.write('callback-%d-%s.state.json'%(n,side),state)
                self.write('callback-%d-%s.observer.json'%(n,side),observer)
        for n,(kind,step) in enumerate(zip([5,1,1,2,3],[2,3,17,18,19]),1):
            self.write('display-query-step-%d.json'%n,dict(nonce=NONCE,kind=kind,runtime_step=step,
                actor_stats_and_cache_bytes_unchanged=kind!=2,calling_thread_rng_before_available=True,
                calling_thread_rng_after_available=True,calling_thread_rng_unchanged=kind!=5,
                feature_flag_restored=True,controlled_3e_rejection=False,python_step_nanoseconds=100))

    def validate(self):
        return validation.validate_stage(self.path,(1,1),expected_nonce=NONCE,expected_input=self.bundle)

    def mutate(self,name,callback):
        value=self.read(name);callback(value);self.write(name,value)

    def test_accepts_bounded_armed_scope(self):
        result=self.validate();self.assertTrue(result['actual_dual_wield'])
        self.assertEqual(result['display_api_calls'],256)
        self.assertFalse(result['original_armed_combat_math_oracle'])

    def test_rejects_changed_fixture_item(self):
        self.mutate('before.state.json',lambda r:r['party'][0]['inventory']['items'][0].update(resref='SW1H02'))
        with self.assertRaisesRegex(ValueError,'physical weapon'):self.validate()

    def test_rejects_stale_input(self):
        self.mutate('armed-input.json',lambda r:r['row']['spec'].update(id='stale'))
        with self.assertRaisesRegex(ValueError,'input drift'):self.validate()

    def test_rejects_pure_rng_draw(self):
        self.mutate('display-query-step-2.json',lambda r:r.update(calling_thread_rng_unchanged=False))
        with self.assertRaisesRegex(ValueError,'RNG'):self.validate()

    def test_rejects_insensitive_rng_control(self):
        self.mutate('display-query-step-1.json',lambda r:r.update(calling_thread_rng_unchanged=True))
        with self.assertRaisesRegex(ValueError,'RNG'):self.validate()

    def test_rejects_actor_byte_mutation(self):
        self.mutate('display-query-step-3.json',lambda r:r.update(actor_stats_and_cache_bytes_unchanged=False))
        with self.assertRaisesRegex(ValueError,'actor/cache bytes'):self.validate()

    def test_rejects_deferred_gui_cache_mutation(self):
        self.mutate('capture-7.observer.json',lambda r:r['actors'][0].update(cached_thac0=13))
        with self.assertRaisesRegex(ValueError,'changed caches'):self.validate()

    def test_rejects_changed_gui_world(self):
        self.mutate('capture-4.state.json',lambda r:r.update(game_time=13))
        with self.assertRaisesRegex(ValueError,'changed collected world'):self.validate()

    def test_rejects_wrong_actual_headline(self):
        self.mutate('capture-3.ui.json',lambda r:r['controls'][4].update(text='14'))
        with self.assertRaisesRegex(ValueError,'headline/parity'):self.validate()

    def test_rejects_missing_portrait_callback(self):
        (self.path/'callback-2.json').unlink()
        with self.assertRaisesRegex(ValueError,'portrait callbacks'):self.validate()

    def test_rejects_extra_legacy_world_mutation(self):
        self.mutate('capture-8.state.json',lambda r:r.update(game_time=13))
        with self.assertRaisesRegex(ValueError,'additional world changes'):self.validate()

    def test_rejects_stale_native_nonce(self):
        self.mutate('display-query-step-2.json',lambda r:r.update(nonce='a'*32))
        with self.assertRaisesRegex(ValueError,'native identity'):self.validate()

    def test_rejects_legacy_result_change(self):
        def change(r):
            next(c for c in r['checks'] if c.get('name')=='armed.legacy-default')['samples'][0]['details']['ToHitStats']['Total']=99
        self.mutate('menu-runtime.json',change)
        with self.assertRaisesRegex(ValueError,'legacy omitted/False parity'):self.validate()

    def test_rejects_insensitive_legacy_byte_control(self):
        self.mutate('display-query-step-4.json',lambda r:r.update(actor_stats_and_cache_bytes_unchanged=True))
        with self.assertRaisesRegex(ValueError,'control insensitive'):self.validate()

    def test_rejects_inconsistent_legacy_cache(self):
        self.mutate('after.observer.json',lambda r:r['actors'][0].update(cached_thac0=14))
        with self.assertRaisesRegex(ValueError,'cache/result inconsistent'):self.validate()

    def test_rejects_wrong_die_roll_control(self):
        def change(r):
            next(c for c in r['checks'] if c.get('name')=='armed.rng-control')['result']=0
        self.mutate('menu-runtime.json',change)
        with self.assertRaisesRegex(ValueError,'die-roll'):self.validate()

    def test_rejects_missing_enabled_game_profile(self):
        self.mutate('menu-host-result.json',lambda r:r.update(style_thac0_flag_loaded=False))
        with self.assertRaisesRegex(ValueError,'style profile'):self.validate()

    def test_rejects_unrequested_old_style_path(self):
        self.mutate('menu-host-result.json',lambda r:r.update(style_thac0_flag_effective=False,legacy_style_control=True))
        with self.assertRaisesRegex(ValueError,'style profile'):self.validate()

    def test_accepts_declared_flag_off_boundary_control(self):
        self.bundle['legacy_style_control']=True;self.write('armed-input.json',self.bundle)
        self.mutate('menu-host-result.json',lambda r:r.update(style_thac0_flag_effective=False,legacy_style_control=True))
        result=self.validate();self.assertTrue(result['legacy_style_control'])
        self.assertFalse(result['style_thac0_penalties_enabled'])

    def test_rejects_inactive_declared_stat(self):
        self.bundle['actor1_stat_expectations']={'114':1};self.write('armed-input.json',self.bundle)
        with self.assertRaisesRegex(ValueError,'stat/effect not active'):self.validate()

    def test_rejects_missing_declared_effect(self):
        self.bundle['actor1_effect_expectations']=[dict(source_ref='RDXRANK',opcode=233,parameters=[1,114])]
        self.write('armed-input.json',self.bundle)
        with self.assertRaisesRegex(ValueError,'effect missing/wrong'):self.validate()

    def test_rejects_zero_proficiency_case_claimed_nonzero(self):
        self.bundle['nonzero_proficiency_damage']=True;self.write('armed-input.json',self.bundle)
        with self.assertRaisesRegex(ValueError,'nonzero proficiency'):self.validate()


if __name__=='__main__':unittest.main()
