import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('private_game_test', Path(__file__).resolve().parents[1] / 'private_game.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class PrivateRootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'chitin.key').write_bytes(b'KEY fixture')
        (self.source / 'engine.lua').write_bytes(b'original config')
        self.private = self.root / 'private'

    def tearDown(self): self.temp.cleanup()

    def test_saveconfig_is_private_and_preserved(self):
        receipt = helper.prepare(self.source, self.private)
        (self.private / 'gem-baldur.ini').write_bytes(b'saved settings')
        result = helper.validate(receipt)
        self.assertTrue(result['clean_game_root_hashes_unchanged'])
        self.assertFalse((self.source / 'gem-baldur.ini').exists())
        self.assertIn('gem-baldur.ini', result['allowed_private_root_changes'])
        self.assertFalse(result['linked_asset_content_fully_hashed'])

    def test_changed_key_or_unexpected_root_file_fails(self):
        receipt = helper.prepare(self.source, self.private)
        (self.private / 'chitin.key').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Unexpected private game write'):
            helper.validate(receipt)
        (self.private / 'chitin.key').write_bytes(b'KEY fixture')
        (self.private / 'unexpected.txt').write_bytes(b'write')
        with self.assertRaisesRegex(ValueError, 'Unexpected private game write'):
            helper.validate(receipt)

    def test_source_changes_and_missing_private_input_fail(self):
        receipt = helper.prepare(self.source, self.private)
        (self.source / 'new.ini').write_bytes(b'outside write')
        with self.assertRaisesRegex(ValueError, 'Protected clean-game'):
            helper.validate(receipt)
        (self.source / 'new.ini').unlink()
        (self.private / 'engine.lua').unlink()
        with self.assertRaisesRegex(ValueError, 'disappeared'):
            helper.validate(receipt)

    def test_unexpected_private_directory_and_unsafe_source_rejected(self):
        (self.source / 'save').mkdir()
        with self.assertRaisesRegex(ValueError, 'Unapproved source directory'):
            helper.prepare(self.source, self.private)
        (self.source / 'save').rmdir()
        receipt = helper.prepare(self.source, self.private)
        (self.private / 'save').mkdir()
        with self.assertRaisesRegex(ValueError, 'Unexpected private game node'):
            helper.validate(receipt)

    def test_existing_or_nested_destination_is_never_reused(self):
        with self.assertRaises(ValueError):
            helper.prepare(self.source, self.source / 'private')
        self.private.mkdir()
        with self.assertRaises(ValueError):
            helper.prepare(self.source, self.private)


if __name__ == '__main__': unittest.main()
