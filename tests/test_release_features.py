import json
from pathlib import Path
import tempfile
import unittest
from preferences import Preferences
from platform_backend import elapsed_idle

class ReleaseTests(unittest.TestCase):
    def test_intro_shown_once_and_can_be_replayed(self):
        with tempfile.TemporaryDirectory() as d:
            prefs=Preferences(Path(d)/'state.json')
            self.assertFalse(prefs.intro_complete())
            prefs.complete_intro()
            self.assertTrue(Preferences(Path(d)/'state.json').intro_complete())
    def test_corrupt_preferences_show_intro(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'state.json'; path.write_text('{bad')
            self.assertFalse(Preferences(path).intro_complete())
    def test_windows_idle_wraparound(self):
        self.assertEqual(elapsed_idle(25,0xFFFFFFF0),.041)
        self.assertEqual(elapsed_idle(3500,1000),2.5)
    def test_invalid_resume_file_is_preserved(self):
        from auto_typer import AutoTyper
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'document.txt';path.write_text('Important local document')
            app=AutoTyper.__new__(AutoTyper);app.tell=lambda *args:None
            app.restore_state(path)
            self.assertTrue(path.exists())
