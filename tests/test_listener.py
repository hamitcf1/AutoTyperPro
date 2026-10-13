import unittest
from platform_backend import wait_for_listener

class Listener:
    def __init__(self,alive,ready,loop): self.alive=alive; self._ready=ready; self._loop=loop; self.stopped=False
    def is_alive(self): return self.alive
    def stop(self): self.stopped=True

class ListenerTests(unittest.TestCase):
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
