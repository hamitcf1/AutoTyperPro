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
    def test_invalid_typing_types_never_overwrite_existing_profile(self):
        from profiles import ProfileStore, new_profile
        with tempfile.TemporaryDirectory() as directory:
            store=ProfileStore(Path(directory)/'profiles.json')
            profile=new_profile('Original','typing',{})
            store.save(profile);before=store.path.read_bytes()
            imported=Path(directory)/'import.json'
            for config in ({'natural':'not-a-boolean'},{'word_pauses':1},{'min_ms':10.5},{'delay_ms':True},{'delay_ms':1},{'start_delay':False}):
                profile['config']=config
                imported.write_text(json.dumps({'schema':1,'profile':profile}))
                with self.assertRaises(ValueError):store.import_file(imported)
                self.assertEqual(store.path.read_bytes(),before)
    def test_activity_modifier_lists_round_trip_as_ui_configuration(self):
        from profiles import ProfileStore, new_profile
        with tempfile.TemporaryDirectory() as directory:
            store=ProfileStore(Path(directory)/'profiles.json')
            store.save(new_profile('Shortcut','activity',{'key':'f18','modifiers':['control']}))
            self.assertEqual(store.load()[0]['config'],{'idle_threshold':60,'interval':30,'distance':1,'movement':'horizontal_return','duration_ms':80,'key':'f18','modifiers':('control',)})
    def test_rename_delete_and_invalid_config(self):
        from profiles import ProfileStore, new_profile
        with tempfile.TemporaryDirectory() as directory:
            store = ProfileStore(Path(directory) / 'profiles.json')
            profile = new_profile('My profile','activity',{})
            store.save(profile); profile['name']='Renamed';store.save(profile)
            self.assertEqual([p['name'] for p in store.load()], ['Renamed'])
            with self.assertRaises(ValueError): store.save(new_profile('Invalid','activity',{'interval':0}))
            store.delete(profile['id']);self.assertEqual(store.load(), [])
