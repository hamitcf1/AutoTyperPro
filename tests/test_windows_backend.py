import ctypes as C
import threading
import unittest
from platform_backend import WindowsBackend, WinPoint, WinRect

class FakeWindows(WindowsBackend):
    def __init__(self, moved=False):
        self.lock=threading.Lock();self.moves=[];self.calls=0;self.moved=moved
        self.scan_code=lambda vk,mode:{0x10:0x2A,0xA0:0x2A,0x0D:0x1C,0x1B:1}.get(vk,0)
    def position(self):
        self.calls+=1
        return WinPoint(99,20) if self.calls==1 else WinPoint(50,50) if self.moved else WinPoint(98,20)
    def monitor_at(self,point,flags):return 1
    def monitor_info(self,handle,info):info._obj.monitor=WinRect(0,0,100,100);return True
    def move_to(self,point):self.moves.append(tuple(point) if isinstance(point,tuple) else (point.x,point.y))

class WindowsTests(unittest.TestCase):
    def test_physical_keys_include_hardware_scan_codes(self):
        b=FakeWindows();record=[]
        def send(count,events,size):
            record.extend((events[i].payload.keyboard.vk,events[i].payload.keyboard.scan,events[i].payload.keyboard.flags) for i in range(count));return count
        b.send_input=send;b.newline();b.press(0x1B)
        self.assertEqual([scan for vk,scan,flags in record],[0x2A,0x1C,0x1C,0x2A,1,1])
        self.assertEqual([flags for vk,scan,flags in record],[0,0,2,2,0,2])
    def test_extended_physical_keys_include_extended_flag(self):
        backend=FakeWindows();received=[]
        def send(count,events,size):
            received.extend(events[i].payload.keyboard.flags for i in range(count));return count
        backend.send_input=send
        backend.physical_key_event(0x27,True);backend.physical_key_event(0x27,False)
        self.assertEqual(received,[1,3])
    def test_keyboard_injection_rejection_is_reported(self):
        b=FakeWindows();b.send_input=lambda *args:0
        with self.assertRaises(RuntimeError):b.write('İ')
    def test_windows_unicode_emits_utf16_units(self):
        b=FakeWindows();record=[]
        def send(count,events,size):
            record.extend((events[i].payload.keyboard.scan,events[i].payload.keyboard.flags) for i in range(count));return count
        b.send_input=send;b.write('İ🙂')
        self.assertEqual(record,[(0x130,4),(0x130,6),(0xD83D,4),(0xD83D,6),(0xDE42,4),(0xDE42,6)])
    def test_edge_and_restore(self):
        b=FakeWindows();self.assertTrue(b.micro_activity(False,threading.Event()));self.assertEqual(b.moves,[(98,20),(99,20)])
    def test_user_move_is_preserved(self):
        b=FakeWindows(True);b.micro_activity(False,threading.Event());self.assertEqual(b.moves,[(98,20)])
    def test_stop_prevents_input(self):
        b=FakeWindows();stop=threading.Event();stop.set();self.assertFalse(b.micro_activity(False,stop));self.assertEqual(b.moves,[])
    def test_windows_idle_reads_native_counter(self):
        b=FakeWindows();b.ticks=lambda:3500
        def last_input(info):info._obj.time=1000;return True
        b.last_input=last_input
        self.assertEqual(b.idle_seconds(),2.5)
