import math
import queue
import threading
import unittest
from engine import TypingConfig, JigglerConfig, type_text, JigglerSchedule

class Backend:
    def __init__(self): self.output = []; self.stop = None
    def write(self, text):
        self.output.append(text)
        if self.stop: self.stop.set()
    def newline(self): self.output.append('<shift-enter>')

class EngineTests(unittest.TestCase):
    def test_unicode_and_newlines(self):
        for mode, expected in [('space', ['İ', ' ', 'ş']), ('ignore', ['İ', 'ş']), ('shift_enter', ['İ', '<shift-enter>', 'ş'])]:
            b = Backend(); q = queue.Queue()
            type_text('İ\nş', TypingConfig(delay_ms=30, start_delay=0, newline=mode), b, threading.Event(), q)
            self.assertEqual(b.output, expected)
            events = list(q.queue)
            self.assertEqual(events[-1][0], 'finished')
            self.assertEqual([x for x in events if x[0] == 'progress'][-1][1], 3)
    def test_invalid_settings(self):
        for value in [math.nan, math.inf, -1, 61]:
            with self.assertRaises(ValueError): TypingConfig(start_delay=value).validate()
        with self.assertRaises(ValueError): TypingConfig(min_ms=500, max_ms=10).validate()
        with self.assertRaises(ValueError): JigglerConfig(interval=0).validate()
        with self.assertRaises(ValueError): JigglerConfig(idle_threshold=math.nan).validate()
    def test_countdown_cancellation(self):
        stop = threading.Event(); stop.set(); b = Backend(); q = queue.Queue()
        type_text('abc', TypingConfig(start_delay=3), b, stop, q)
        self.assertEqual(b.output, [])
        self.assertEqual(list(q.queue)[-1][0], 'stopped')
    def test_cancellation_after_character(self):
        stop = threading.Event(); b = Backend(); b.stop = stop; q = queue.Queue()
        type_text('abc', TypingConfig(start_delay=0), b, stop, q)
        self.assertEqual(b.output, ['a'])
        self.assertEqual(list(q.queue)[-1][0], 'stopped')
    def test_worker_error_is_reported(self):
        class Broken(Backend):
            def write(self, text): raise RuntimeError('permission denied')
        q = queue.Queue()
        type_text('a', TypingConfig(start_delay=0), Broken(), threading.Event(), q)
        self.assertEqual(list(q.queue)[-1], ('error', 'permission denied'))
    def test_jiggler_schedule(self):
        s = JigglerSchedule(JigglerConfig(idle_threshold=60, interval=30))
        self.assertFalse(s.due(0, 59, False))
        self.assertTrue(s.due(1, 60, False)); s.record(1)
        self.assertFalse(s.due(20, 80, False))
        self.assertFalse(s.due(32, 90, True))
        self.assertTrue(s.due(32, 90, False))
        self.assertFalse(s.due(70, 2, False))
    def test_estimate_transformed_text(self):
        c = TypingConfig(start_delay=0, delay_ms=100, newline='ignore', word_pauses=True)
        self.assertAlmostEqual(c.estimate('a\nb c'), .6)

if __name__ == '__main__': unittest.main()
