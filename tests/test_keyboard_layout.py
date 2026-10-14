import threading
import unittest
from keyboard_layout import build_keymap,current_keymap
from remote_focus import is_remote_client

class KeyboardLayoutTests(unittest.TestCase):
    def test_map_selects_simplest_gesture_and_supports_dead_keys(self):
        def translate(code,state,pending):
            if pending==1:return ('é',0) if code==14 and state==0 else ('',1)
            if code==14 and state==0:return 'e',0
            if code==14 and state==2:return 'E',0
            if code==14 and state==8:return '',1
            if code==11 and state in (0,2):return 'b',0
            if code==12 and state==0:return 'ab',0
            return '',0
        mapping=build_keymap(translate)
        self.assertEqual(mapping['b'],((11,()),))
        self.assertEqual(mapping['E'],((14,(56,)),))
        self.assertEqual(mapping['é'],((14,(58,)),(14,())))
        self.assertNotIn('ab',mapping)
    def test_worker_rejects_layout_lookup_before_loading_carbon(self):
        errors=[]
        def run():
            try:current_keymap()
            except Exception as exc:errors.append(exc)
        worker=threading.Thread(target=run);worker.start();worker.join()
        self.assertIsInstance(errors[0],RuntimeError)
        self.assertIn('main thread',str(errors[0]))
    def test_remote_detection_does_not_match_ordinary_application(self):
        self.assertTrue(is_remote_client('/System/Applications/Utilities/Screen Sharing.app/Contents/MacOS/Screen Sharing'))
        self.assertFalse(is_remote_client('/Applications/TextEdit.app/Contents/MacOS/TextEdit'))
