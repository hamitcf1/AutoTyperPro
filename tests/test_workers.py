import queue
import threading
import time
import unittest
from engine import JigglerConfig, jiggle, TypingConfig, type_text

class WorkerTests(unittest.TestCase):
    def test_stop_interrupts_live_countdown(self):
        class Backend:
            def write(self, text): raise AssertionError('Must not type during countdown')
        stop = threading.Event(); events = queue.Queue()
        thread = threading.Thread(target=type_text,args=('abc',TypingConfig(start_delay=60),Backend(),stop,events))
        thread.start(); self.assertEqual(events.get(timeout=1)[0], 'countdown')
        stop.set(); thread.join(.5); self.assertFalse(thread.is_alive())
        self.assertEqual(list(events.queue)[-1][0], 'stopped')
    def test_jiggler_stops_and_emits_movement(self):
        stop = threading.Event(); events = queue.Queue()
        class Backend:
            def idle_seconds(self): return 100
            def micro_activity(self, f18, cancellation):
                stop.set(); return True
        thread = threading.Thread(target=jiggle,args=(JigglerConfig(),Backend(),stop,lambda:False,events))
        thread.start(); thread.join(.5)
        self.assertFalse(thread.is_alive()); self.assertIn(('movement',1),list(events.queue))
        self.assertEqual(list(events.queue)[-1][0],'jiggler_stopped')
    def test_jiggler_yields_to_typing(self):
        stop = threading.Event(); events = queue.Queue()
        class Backend:
            def idle_seconds(self): stop.set(); return 100
            def micro_activity(self, f18, cancellation): raise AssertionError('Must yield to typing')
        jiggle(JigglerConfig(),Backend(),stop,lambda:True,events)
        self.assertEqual(list(events.queue)[-1][0],'jiggler_stopped')
    def test_jiggler_reports_backend_error(self):
        class Backend:
            def idle_seconds(self): raise RuntimeError('idle unavailable')
        events = queue.Queue()
        jiggle(JigglerConfig(),Backend(),threading.Event(),lambda:False,events)
        self.assertEqual(list(events.queue)[-1],('jiggler_error','idle unavailable'))

if __name__ == '__main__': unittest.main()
