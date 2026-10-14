import tempfile
from pathlib import Path
import unittest
from preferences import Preferences
class DesktopPreferenceTests(unittest.TestCase):
    def test_desktop_choices_are_explicit_and_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            prefs=Preferences(Path(directory)/'preferences.json')
            self.assertFalse(prefs.load().get('notifications',True))
            self.assertFalse(prefs.load().get('keep_running',True))
            prefs.update({'notifications':True,'keep_running':True,'reduced_motion':False})
            self.assertTrue(Preferences(prefs.path).load()['notifications'])
            self.assertTrue(Preferences(prefs.path).load()['keep_running'])
            with self.assertRaises(ValueError):prefs.update({'notifications':'yes'})
