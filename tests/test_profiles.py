import json
from pathlib import Path
import tempfile
import unittest
from preferences import Preferences

class PreferenceTests(unittest.TestCase):
    def test_defaults_and_intro_migration_survive_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'preferences.json'
            prefs = Preferences(path)
            self.assertEqual(prefs.load()['locale'], 'en')
            self.assertEqual(prefs.load()['appearance'], 'dark')
            path.write_text('{"intro_complete":true}')
            prefs.update({'locale':'tr', 'appearance':'light'})
            self.assertTrue(Preferences(path).intro_complete())
            self.assertEqual(Preferences(path).load()['locale'], 'tr')
    def test_invalid_preferences_do_not_overwrite_saved_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            prefs = Preferences(Path(directory) / 'prefs.json')
            prefs.update({'locale':'tr'})
            before = prefs.path.read_bytes()
            with self.assertRaises(ValueError): prefs.update({'locale':'xx'})
            self.assertEqual(prefs.path.read_bytes(), before)

class ProfileTests(unittest.TestCase):
    def test_profile_export_import_round_trip(self):
        from profiles import ProfileStore, new_profile
        with tempfile.TemporaryDirectory() as directory:
            store = ProfileStore(Path(directory) / 'profiles.json')
            profile = new_profile('Writing', 'typing', {'delay_ms':100})
            store.save(profile)
            exported = Path(directory) / 'writing.json'
            store.export_file(profile, exported)
            imported = store.import_file(exported)
            self.assertEqual(imported['name'], 'Writing')
            self.assertEqual(imported['config']['delay_ms'], 100)
            self.assertEqual(len(store.load()), 1)
    def test_invalid_import_leaves_existing_profiles_unchanged(self):
        from profiles import ProfileStore, new_profile
        with tempfile.TemporaryDirectory() as directory:
            store = ProfileStore(Path(directory) / 'profiles.json')
            store.save(new_profile('Gentle', 'activity', {}))
            before = store.path.read_bytes()
            exported = Path(directory) / 'bad.json'
            for payload in ('{broken', '[]', '{"schema":99,"profile":{}}', '{"schema":1,"profile":{"name":"bad"}}'):
                exported.write_text(payload)
                with self.assertRaises(ValueError): store.import_file(exported)
                self.assertEqual(store.path.read_bytes(), before)
    def test_rename_delete_and_invalid_config(self):
        from profiles import ProfileStore, new_profile
        with tempfile.TemporaryDirectory() as directory:
            store = ProfileStore(Path(directory) / 'profiles.json')
            profile = new_profile('My profile','activity',{})
            store.save(profile); profile['name']='Renamed';store.save(profile)
            self.assertEqual([p['name'] for p in store.load()], ['Renamed'])
            with self.assertRaises(ValueError): store.save(new_profile('Invalid','activity',{'interval':0}))
            store.delete(profile['id']);self.assertEqual(store.load(), [])
