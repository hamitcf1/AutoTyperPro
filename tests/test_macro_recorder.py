import queue
import unittest
from unittest.mock import patch

class Listener:
    def stop(self):pass
    def join(self,timeout=None):pass
class Backend:
    native_platform='darwin'
    def display_layout(self):return [{'left':0,'top':0,'width':100,'height':100}]
    def listen_events(self,callback,capture):self.callback=callback;return Listener()

class RecorderTests(unittest.TestCase):
    def test_movement_only_filters_input_and_coalesces_samples(self):
        from macro_recorder import Recorder
        now=[100.0]
        with patch('macro_recorder.time.monotonic',side_effect=lambda:now[0]):
            backend=Backend();recorder=Recorder(backend,frozenset({'move'}),queue.Queue());recorder.start()
            backend.callback('key',{'code':0,'down':True})
            backend.callback('button',{'button':'left','down':True,'x':1,'y':1})
            backend.callback('move',{'x':1,'y':1})
            now[0]=100.01;backend.callback('move',{'x':2,'y':2})
            now[0]=100.04;backend.callback('move',{'x':3,'y':3})
            macro=recorder.stop()
            self.assertEqual([(e.kind,e.data) for e in macro.events],[('move',{'x':1,'y':1}),('move',{'x':3,'y':3})])
    def test_escape_excluded_and_held_keys_balanced_on_stop(self):
        from macro_recorder import Recorder
        now=[100.0]
        with patch('macro_recorder.time.monotonic',side_effect=lambda:now[0]):
            backend=Backend();recorder=Recorder(backend,frozenset({'key'}),queue.Queue());recorder.start()
            backend.callback('key',{'code':56,'down':True})
            now[0]=101;backend.callback('key',{'code':53,'down':True})
            macro=recorder.stop()
            self.assertEqual([(e.data['code'],e.data['down']) for e in macro.events],[(56,True),(56,False)])
            self.assertFalse(recorder.active)
    def test_time_limit_finishes_recording_without_input(self):
        from macro_recorder import Recorder
        now=[100.0]
        with patch('macro_recorder.time.monotonic',side_effect=lambda:now[0]):
            backend=Backend();q=queue.Queue();recorder=Recorder(backend,frozenset({'move'}),q);recorder.start()
            backend.callback('move',{'x':1,'y':1})
            now[0]=401
            self.assertTrue(recorder.limit_reached())
            self.assertEqual(q.get()[0],'record_limit')
            self.assertEqual(len(recorder.stop().events),1)
    def test_event_limit_reserves_space_for_releases(self):
        from macro_recorder import Recorder
        now=[100.0]
        with patch('macro_recorder.time.monotonic',side_effect=lambda:now[0]):
            backend=Backend();recorder=Recorder(backend,frozenset({'key','scroll'}),queue.Queue());recorder.start()
            backend.callback('key',{'code':56,'down':True})
            for i in range(10001):backend.callback('scroll',{'dx':0,'dy':1})
            macro=recorder.stop()
            self.assertLessEqual(len(macro.events),10000)
            self.assertEqual(macro.events[-1].data,{'code':56,'down':False})
