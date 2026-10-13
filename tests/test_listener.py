import unittest
from unittest.mock import patch
import threading
from platform_backend import wait_for_listener

class Listener:
    def __init__(self,alive,ready,loop): self.alive=alive; self._ready=ready; self._loop=loop; self.stopped=False
    def is_alive(self): return self.alive
    def stop(self): self.stopped=True

class ListenerTests(unittest.TestCase):
    def test_mac_escape_listener_never_imports_keyboard_layout_library(self):
        from platform_backend import MacBackend
        backend = MacBackend.__new__(MacBackend)
        listener = Listener(True, True, object())
        listener.start = lambda: None
        with patch('platform_backend.MacEscapeListener', return_value=listener, create=True) as factory:
            with patch('builtins.__import__', side_effect=AssertionError('No pynput imports permitted')):
                backend.listen_escape(lambda: None)
        factory.assert_called_once()
    def test_native_listener_uses_only_escape_virtual_key(self):
        from platform_backend import MacEscapeListener
        listener = MacEscapeListener.__new__(MacEscapeListener)
        listener._stop_event = threading.Event()
        seen = []; listener.callback = lambda: seen.append('escape')
        listener.keycode = lambda event, field: event
        self.assertEqual(listener.handle_event(None, 10, 53, None), 53)
        listener.handle_event(None, 10, 0, None)
        listener.handle_event(None, 11, 53, None)
        listener._stop_event.set(); listener.handle_event(None, 10, 53, None)
        self.assertEqual(seen, ['escape'])
    def test_dead_listener_is_rejected(self):
        listener=Listener(False,True,None)
        with self.assertRaises(RuntimeError): wait_for_listener(listener,mac=True,timeout=.01)
        self.assertTrue(listener.stopped)
    def test_missing_event_tap_is_rejected(self):
        listener=Listener(True,True,None)
        with self.assertRaises(RuntimeError): wait_for_listener(listener,mac=True,timeout=.01)
        self.assertTrue(listener.stopped)
    def test_listener_startup_timeout_is_bounded(self):
        listener=Listener(True,False,None)
        with self.assertRaises(RuntimeError): wait_for_listener(listener,mac=True,timeout=.01)
    def test_ready_listener_is_accepted(self):
        listener=Listener(True,True,object())
        wait_for_listener(listener,mac=True,timeout=.01)
        self.assertFalse(listener.stopped)
