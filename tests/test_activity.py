import threading
import unittest
from engine import JigglerConfig

class ActivityTests(unittest.TestCase):
    def test_bounds_and_disabled_activity_validation(self):
        for data in ({'distance':0},{'distance':101},{'duration_ms':49},{'duration_ms':1001},{'movement':'off','key':None},{'key':'escape'},{'key':'shift'},{'key':'f18','modifiers':('unknown',)}):
            with self.subTest(data=data),self.assertRaises(ValueError):JigglerConfig(**data).validate()
    def test_presets_and_legacy_f18_migration(self):
        from activity import PRESETS, migrate_activity
        self.assertEqual((PRESETS['gentle'].distance,PRESETS['gentle'].idle_threshold,PRESETS['gentle'].key),(1,60,None))
        self.assertEqual((PRESETS['balanced'].distance,PRESETS['balanced'].interval),(4,60))
        self.assertEqual((PRESETS['keyboard'].movement,PRESETS['keyboard'].key),('off','f18'))
        self.assertEqual(migrate_activity({'f18':True})['key'],'f18')
    def test_path_stays_on_current_display(self):
        from activity import activity_path
        path=activity_path((99,99),(0,0,100,100),JigglerConfig(distance=100,movement='square'))
        self.assertEqual(path,[(0,99),(0,0),(99,0)])
    def test_real_user_movement_cancels_restore(self):
        from activity import perform_activity
        class Backend:
            def __init__(self):self.positions=iter([(50,50),(20,20)]);self.moves=[]
            def position(self):return next(self.positions)
            def screen_bounds(self,point):return (0,0,100,100)
            def move_to(self,point):self.moves.append(point)
            def key_chord(self,*args):raise AssertionError('No key activity expected')
        backend=Backend();perform_activity(backend,JigglerConfig(distance=4),threading.Event())
        self.assertEqual(backend.moves,[(54,50)])

class ChordTests(unittest.TestCase):
    def test_cancellation_releases_modifier_before_returning(self):
        from native_keys import KeyChordMixin
        stop=threading.Event()
        class Backend(KeyChordMixin):
            native_platform='darwin'
            def __init__(self):self.events=[]
            def physical_key_event(self,code,down):
                self.events.append((code,down))
                if down:stop.set()
        backend=Backend();backend.key_chord('a',('shift','control'),stop)
        self.assertEqual(backend.events,[(56,True),(56,False)])
    def test_injection_failure_releases_all_attempted_keys(self):
        from native_keys import KeyChordMixin
        class Backend(KeyChordMixin):
            native_platform='win32'
            def __init__(self):self.events=[]
            def physical_key_event(self,code,down):
                self.events.append((code,down))
                if down and code==65:raise RuntimeError('Rejected')
        backend=Backend()
        with self.assertRaises(RuntimeError):backend.key_chord('a',('control',),threading.Event())
        self.assertEqual(backend.events,[(162,True),(65,True),(65,False),(162,False)])
