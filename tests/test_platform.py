import threading
import unittest
from platform_backend import MacBackend, Point, Rect, Size

class SimulatedMac(MacBackend):
    def __init__(self, user_moves=False, permitted=True):
        self.lock = threading.Lock(); self.position_calls = 0; self.user_moves = user_moves; self.permitted = permitted
        self.sent = []; self.keys = []
    def allowed(self): return self.permitted
    def position(self):
        self.position_calls += 1
        return Point(99,20) if self.position_calls == 1 else Point(50,50) if self.user_moves else Point(98,20)
    def displays(self, origin, limit, display, count):
        display._obj.value = 1; count._obj.value = 1; return 0
    def bounds(self, display): return Rect(Point(0,0),Size(100,100))
    def mouse(self, source, kind, position, button): return (position.x,position.y)
    def send(self,event): self.sent.append(event)
    def press(self, code, flags=0): self.keys.append(code)

class PlatformTests(unittest.TestCase):
    def test_unicode_events_clear_inherited_modifier_flags(self):
        backend=SimulatedMac(); flags=[]
        backend.key=lambda source,code,down: object()
        backend.unicode=lambda event,length,units: None
        backend.flags=lambda event,value: flags.append(value)
        backend.write('İ')
        self.assertEqual(flags,[0,0])
    def test_boundary_and_restore(self):
        backend = SimulatedMac(); self.assertTrue(backend.micro_activity(False,threading.Event()))
        self.assertEqual(backend.sent,[(98,20),(99,20)]); self.assertEqual(backend.keys,[])
    def test_user_movement_is_not_overwritten(self):
        backend = SimulatedMac(user_moves=True); backend.micro_activity(False,threading.Event())
        self.assertEqual(backend.sent,[(98,20)])
    def test_optional_f18(self):
        backend = SimulatedMac(); backend.micro_activity(True,threading.Event()); self.assertEqual(backend.keys,[79])
    def test_permission_denial(self):
        backend = SimulatedMac(permitted=False)
        with self.assertRaises(PermissionError): backend.micro_activity(False,threading.Event())
        self.assertEqual(backend.sent,[])
    def test_cancel_prevents_movement(self):
        backend = SimulatedMac(); stop=threading.Event(); stop.set()
        self.assertFalse(backend.micro_activity(False,stop)); self.assertEqual(backend.sent,[])

if __name__ == '__main__': unittest.main()
