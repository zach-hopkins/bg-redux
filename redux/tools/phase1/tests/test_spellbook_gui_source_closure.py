"""Execute actual closure builders without importing native/build/run adapters."""
import ast
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('closure_menu_harness',HERE/'menu_harness.py')
menu=importlib.util.module_from_spec(spec);spec.loader.exec_module(menu)
REQUIRED=('gemrb/GUIScripts/EESpellbookInformation.py','gemrb/GUIScripts/EESpellbookHeading.py',
          'gemrb/GUIScripts/BG2EEConfirmation.py','gemrb/GUIScripts/GUIOPT.py',
          'gemrb/GUIScripts/GUIOPTControls.py','gemrb/unhardcoded/shared/defaults.ini')

def closure(name,function,source):
    path=HERE/name;tree=ast.parse(path.read_text(encoding='utf8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==function]
    if len(nodes)!=1:raise ValueError('Actual closure builder absent/ambiguous')
    scope=dict(Path=Path,HERE=HERE,__file__=str(path),sys=types.SimpleNamespace(modules={}),
        common=types.SimpleNamespace(sources=lambda project:[]),menu=menu)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope)
    if function in ('menu_source_inputs','hotkey_source_inputs'):return scope[function](source)
    return scope[function](source.parent,source)

class ImportedGUIClosureTests(unittest.TestCase):
    def test_eight_actual_adapters_require_new_modules_and_persistent_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'candidate'
            specs=[('menu_harness.py','menu_source_inputs'),('hotkey_harness.py','hotkey_source_inputs')]+[(name,'sources')for name in
                ('spellbook_operation_journey.py','spellbook_erase_journey.py','cell_recruitment_journey.py',
                 'minsc_recruitment_journey.py','jaheira_dialogue_journey.py','spell_cast_journey.py')]
            for name,function in specs:
                with self.subTest(adapter=name):
                    actual=set(closure(name,function,source))
                    self.assertTrue({source/relative for relative in REQUIRED}.issubset(actual))
    def test_actual_freezer_rejects_missing_inputs_and_retains_bytes_both_drift_directions(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);paths=[root/name for name in REQUIRED]
            with self.assertRaises(FileNotFoundError):menu.freeze_source_inputs(paths,root/'missing')
            for index,path in enumerate(paths):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(('independent resource %d'%index).encode())
            pins,copies=menu.freeze_source_inputs(paths,root/'receipt')
            for path in paths:
                key=str(path.resolve());frozen=Path(copies[key]['frozen']);before=path.read_bytes()
                self.assertEqual(frozen.read_bytes(),before);self.assertEqual(menu.sha(frozen),pins[key])
                path.write_bytes(before+b' changed-current')
                self.assertNotEqual(menu.sha(path),pins[key]);self.assertEqual(menu.sha(frozen),pins[key])
                frozen.write_bytes(before+b' changed-frozen')
                self.assertNotEqual(menu.sha(frozen),pins[key])

if __name__=='__main__':unittest.main()
