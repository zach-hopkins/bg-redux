"""Independent page contract negatives; no GemRB import or runtime launch."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import spellbook_information_validation as v

def page_fixture(shown=None,pack='GUIMG',actor=2,kind=1,level=0,top=0):
    shown=shown if shown is not None else [dict(original_index=i,resref='SPELL%03d'%i,name='localized %d'%i)for i in range(31)]
    visible=shown[top:top+7];n=len(shown)
    text='%d/%d (%d-%d/%d)'%(top//7+1,max(1,(n+6)//7),top+1 if n else 0,min(n,top+7),n)
    meta=dict(schema=v.SCHEMA,module='/candidate/gemrb/GUIScripts/EESpellbookInformation.py',pack=pack,actor=actor,kind=kind,level=level,page_size=7,top=top,visible_rows=copy.deepcopy(visible),selected=None,
        default_help_strref=39254,resolved_help='complete localized help',information_text='complete localized help',page_text=text,
        action_strref=17189 if pack=='GUIMG'else 17224,resolved_action_label='localized complete action',
        action_text='localized complete action',action_value=0,action_disabled=True,
        selected_description_ref=None,selected_description=None,all_pages_visited=False,per_label_style_observed=False)
    controls=[]
    def add(cid,**fields):
        row=dict(pack=pack,window=2,id=cid,visible=True,disabled=False);row.update(fields);controls.append(row)
    for i in range(24):
        row=visible[i]if i<len(visible)else None
        add(27+i,visible=row is not None,value=row['original_index']if row else 0,tooltip=row['name']if row else '',stored_tooltip=row['name']if row else '',picture_present=bool(row),picture_observable=True,picture_size=[32,32],rect=[112,228+42*i,44,40],flags=2)
        if i<7:add(v.NAME+i,visible=row is not None,value=row['original_index']if row else 0,text=row['name']if row else '',tooltip=row['name']if row else '')
    add(v.COUNT,text=text);add(v.UP,disabled=top==0);add(v.DOWN,disabled=top+7>=n)
    add(v.ACTION,text=meta['action_text'],value=0,disabled=True);add(v.TEXT,text=meta['information_text'])
    add(v.INFO_UP);add(v.INFO_DOWN)
    return meta,controls

class InformationPageValidationTests(unittest.TestCase):
    def setUp(self):self.shown=[dict(original_index=i,resref='SPELL%03d'%i,name='localized %d'%i)for i in range(31)]
    def test_each_of_five_observed_pages_binds_full_list_without_all_pages_claim(self):
        for top in (0,7,14,21,28):
            m,c=page_fixture(self.shown,top=top);r=v.validate_page(m,self.shown,c,'GUIMG',2,1,0)
            self.assertEqual(r['visible_entries'],min(7,31-top));self.assertFalse(r['all_pages_visited'])
    def test_unknown_or_missing_layout_and_bad_offsets_rejected(self):
        for key,value in (('schema','legacy-grid/1'),('top',1),('top',35),('page_size',24),('all_pages_visited',True),('per_label_style_observed',True)):
            m,c=page_fixture(self.shown);m[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',2,1,0)
    def test_wrong_visible_ref_name_index_or_hidden_used_row_fails(self):
        for cid,key,value in ((27,'value',1),(v.NAME,'text','wrong'),(27,'visible',False),(27,'picture_present',False),(27,'picture_size',[0,32])):
            m,c=page_fixture(self.shown);next(r for r in c if r['id']==cid)[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',2,1,0)
        m,c=page_fixture(self.shown);m['visible_rows'][0]['resref']='OTHER'
        with self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',2,1,0)
    def test_blank_truncated_help_and_enabled_unselected_action_fail(self):
        for cid,key,value in ((v.TEXT,'text',''),(v.TEXT,'text','complete'),(v.ACTION,'disabled',False),(v.COUNT,'text','1/1')):
            m,c=page_fixture(self.shown);next(r for r in c if r['id']==cid)[key]=value
            with self.subTest(cid=cid,key=key),self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',2,1,0)
        m,c=page_fixture(self.shown)
        with self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',2,1,0,expected_help='other frozen TLK text')
    def test_empty_ordinary_book_still_requires_default_help(self):
        m,c=page_fixture([],pack='GUIPR',actor=2,kind=0)
        self.assertEqual(v.validate_page(m,[],c,'GUIPR',2,0,0)['total_known'],0)
        next(r for r in c if r['id']==v.TEXT)['text']=''
        with self.assertRaises(ValueError):v.validate_page(m,[],c,'GUIPR',2,0,0)
    def test_provider_actor_and_unsampled_selection_cannot_be_substituted(self):
        m,c=page_fixture(self.shown)
        with self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',3,1,0)
        with self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',2,1,0,expected_module='/wrong/EESpellbookInformation.py')
        m['selected']=copy.deepcopy(self.shown[0])
        with self.assertRaises(ValueError):v.validate_page(m,self.shown,c,'GUIMG',2,1,0)

if __name__=='__main__':unittest.main()
