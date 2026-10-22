"""New active-slot validator test sources; coordinator execution required."""
import copy
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import weapon_slot_journey as journey


class SlotJourneyTests(unittest.TestCase):
    def envelope(self):
        identity,plan=journey.PLANS['main']
        return dict(schema='bg-redux-phase1-active-slot-journey-native/1',scenario='main',nonce='a'*32,
            case_id=identity,repeats=2,completed=True,error='',sender_runtime_id=10002,target_runtime_id=10003,
            steps=[dict(id=i,route=r,expected_main=m,expected_ammo=a)
                                                                    for i,r,m,a in plan])

    def test_complete_new_mode_has_five_main_and_nine_ranged_boundaries(self):
        self.assertEqual(len(journey.journey_envelope(self.envelope(),'02-plus-normal-pfmw','main',2,'a'*32)[1]),5)
        self.assertEqual(len(journey.PLANS['ranged'][1]),9)

    def test_old_mode_stale_nonce_wrong_case_incomplete_and_reordered_rejected(self):
        for key,value in [('schema','bg-redux-phase1-inventory-journey-native/1'),('nonce','b'*32),
                          ('case_id','ammo-plus-pfmw'),('completed',False),('scenario','ranged')]:
            data=self.envelope();data[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                journey.journey_envelope(data,'02-plus-normal-pfmw','main',2,'a'*32)
        data=self.envelope();data['steps'][1],data['steps'][2]=data['steps'][2],data['steps'][1]
        with self.assertRaisesRegex(ValueError,'coverage'):journey.journey_envelope(data,'02-plus-normal-pfmw','main',2,'a'*32)

    def test_missing_or_extra_steps_cannot_be_accepted_as_a_prefix(self):
        for extra in (False,True):
            data=self.envelope()
            if extra:data['steps'].append(copy.deepcopy(data['steps'][-1]))
            else:data['steps'].pop()
            with self.subTest(extra=extra),self.assertRaisesRegex(ValueError,'coverage'):
                journey.journey_envelope(data,'02-plus-normal-pfmw','main',2,'a'*32)

    def action(self):
        return dict(parsed=True,action_id=356,has_objects=False,expression='TransformItem("bow01","bow02")',
            old_item='bow01',new_item='bow02',flags=0,target_count=37,resolved_runtime_id=10002,
            matching_inventory_items=1,matching_slot=35,charges=[0,0,0])

    def test_actual_implicit_sender_action_accepts_multiple_enumerated_actors(self):
        journey.action_guard(self.action(),'bow01','bow02',10002)

    def test_transform_must_target_one_unique_old_item_in_launcher_or_main_slot(self):
        for key,value in [('matching_inventory_items',2),('matching_inventory_items',True),('matching_slot',11),
                          ('resolved_runtime_id',10003),('charges',[40,0,0]),('has_objects',True),('flags',0x2000)]:
            data=self.action();data[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):journey.action_guard(data,'bow01','bow02',10002)

    def resources(self):
        return {ref:dict(resref=ref,flags=44,enchantment=int(ref.endswith('02')),itemtype=15,proficiency=104,
            header_index=0,attack_type=2 if ref.startswith('arow') else 4,location=1,range=100,
            dice_sides=6,dice_thrown=1,damage_bonus=1,damage_type=4,charges=1,recharge_flags=0,
            thac0_bonus=2 if ref=='bow02' else 1) for ref in journey.RESOURCES}

    def test_loaded_metadata_must_match_bound_raw_resource_not_just_resource_name(self):
        raw=self.resources();rows=list(copy.deepcopy(raw).values());journey.resource_guard(rows,raw)
        rows[2]['thac0_bonus']=99
        with self.assertRaisesRegex(ValueError,'raw ITM'):journey.resource_guard(rows,raw)

    def test_resource_duplicates_and_boolean_numeric_forgery_rejected(self):
        raw=self.resources();rows=list(copy.deepcopy(raw).values());rows[-1]=rows[0]
        with self.assertRaises(ValueError):journey.resource_guard(rows,raw)
        rows=list(copy.deepcopy(raw).values());rows[0]['enchantment']=False
        with self.assertRaises(ValueError):journey.resource_guard(rows,raw)

    def cache(self,raw):
        header={k:raw['arow02'][k] for k in ('attack_type','location','damage_type','dice_sides','dice_thrown','damage_bonus','charges','recharge_flags')}
        return dict(hands=[dict(header=header),dict(header=None)],derived_hands=[
            dict(hand=1,range=101,itemtype=15,proficiency=104,selected_header_range=100,
                 selected_header_thac0_bonus=1,launcher_damage_bonus=1,launcher_thac0_bonus=1),
            dict(hand=2,range=0,itemtype=0,proficiency=0,selected_header_range=None,
                 selected_header_thac0_bonus=None,launcher_damage_bonus=0,launcher_thac0_bonus=0)])

    def test_stale_launcher_thac0_rejected_when_ammo_keeps_max_enchantment_one(self):
        raw=self.resources();cache=self.cache(raw)
        journey.derived_guard(cache,raw,'bow01','arow02',None)
        # Both stock bows have damage bonus1; the stale +1-bow THAC0 bonus2
        # must still fail when the selected +1 arrow keeps max enchantment1.
        cache['derived_hands'][0]['launcher_thac0_bonus']=2
        with self.assertRaisesRegex(ValueError,'launcher'):journey.derived_guard(cache,raw,'bow01','arow02',None)

    def test_selected_header_ability_and_derived_range_proficiency_rejected(self):
        raw=self.resources()
        for field,value in [('range',2),('proficiency',0),('launcher_damage_bonus',0),
                            ('selected_header_range',2),('selected_header_thac0_bonus',9)]:
            cache=self.cache(raw);cache['derived_hands'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):journey.derived_guard(cache,raw,'bow01','arow02',None)
        cache=self.cache(raw);cache['hands'][0]['header']['dice_thrown']=2
        with self.assertRaisesRegex(ValueError,'header'):journey.derived_guard(cache,raw,'bow01','arow02',None)

    def test_raw_item_hash_and_header_bounds_and_zero_proficiency_conversion(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary);table=source/'gemrb/unhardcoded/bg2ee/proftype.2da';table.parent.mkdir(parents=True)
            table.write_text('2DA V1.0\n-1\nOLD_PROFICIENCY\n'+''.join(
                '%s -1\n'%(str(i)+'_BOW' if i==15 else str(i)) for i in range(21)))
            blobs={}
            for ref in journey.RESOURCES:
                raw=bytearray(0x72+56);raw[:8]=b'ITM V1  '
                struct.pack_into('<I',raw,0x64,0x72);struct.pack_into('<H',raw,0x68,1)
                struct.pack_into('<H',raw,0x1c,5);raw[0x31]=0
                blobs[ref]=bytes(raw)
            api=types.SimpleNamespace(probe_ui_resources=types.SimpleNamespace(TYPES={},read_resource=lambda ref,kind:(blobs[ref],'private')))
            metadata={ref:dict(sha256=hashlib.sha256(value).hexdigest()) for ref,value in blobs.items()}
            result=journey.raw_resources(api,metadata,source)
            self.assertEqual(result['arow01']['proficiency'],255)
            metadata['arow01']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'hash'):journey.raw_resources(api,metadata,source)
            metadata['arow01']['sha256']=hashlib.sha256(blobs['arow01']).hexdigest()
            changed=bytearray(blobs['arow01']);struct.pack_into('<H',changed,0x68,100)
            blobs['arow01']=bytes(changed);metadata['arow01']['sha256']=hashlib.sha256(changed).hexdigest()
            with self.assertRaisesRegex(ValueError,'bounds'):journey.raw_resources(api,metadata,source)


if __name__=='__main__':unittest.main()
