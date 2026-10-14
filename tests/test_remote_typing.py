import threading
import unittest
from engine import TypingConfig
from platform_backend import MacBackend

class Receiver(MacBackend):
    def __init__(self):
        self.lock=threading.RLock();self.events=[];self.front=(42,'/System/Applications/Utilities/Screen Sharing.app/Contents/MacOS/Screen Sharing')
        self._typing_remote=False;self._keyboard_layout={'b':[(11,())],'A':[(0,(56,))],' ': [(49,())]}
    def allowed(self):return True
    def frontmost_process(self):return self.front
    def key(self,source,code,down):return {'code':code,'down':down,'flags':0}
    def flags(self,event,value):event['flags']=value
    def unicode(self,event,length,units):event['unicode']=bytes(units).decode('utf-16-le')
    def send(self,event):self.events.append(event.copy())
    def received(self):
        keys={0:'a',11:'b',49:' '}
        return ''.join(keys[e['code']].upper() if e['flags']&(1<<17) else keys[e['code']] for e in self.events if e['down'] and e['code'] in keys)

class RemoteTypingTests(unittest.TestCase):
    def test_receiver_ignoring_unicode_gets_real_keys_not_repeated_a(self):
        backend=Receiver();backend.begin_typing('bA',TypingConfig(),threading.Event());backend.write('b');backend.write('A');backend.end_typing()
        self.assertEqual(backend.received(),'bA')
        self.assertFalse(getattr(backend,'_held_keys',set()))
    def test_unrepresentable_character_is_rejected_before_any_input(self):
        backend=Receiver()
        with self.assertRaises(ValueError):backend.begin_typing('b🙂',TypingConfig(),threading.Event())
        self.assertEqual(backend.events,[])
    def test_remote_focus_loss_stops_instead_of_typing_in_another_app(self):
        backend=Receiver();backend.begin_typing('b',TypingConfig(),threading.Event())
        backend.front=(9,'/Applications/Other.app/Contents/MacOS/Other')
        with self.assertRaises(RuntimeError):backend.write('b')
        self.assertEqual(backend.events,[])
    def test_local_app_keeps_unicode_delivery(self):
        backend=Receiver();backend.front=(9,'/Applications/TextEdit.app/Contents/MacOS/TextEdit')
        backend.begin_typing('🙂',TypingConfig(),threading.Event());backend.write('🙂');backend.end_typing()
        self.assertEqual([event['unicode'] for event in backend.events],['🙂','🙂'])
    def test_remote_newline_does_not_escape_focus_guard(self):
        backend=Receiver();backend.begin_typing('b\n',TypingConfig(newline='shift_enter'),threading.Event())
        backend.front=(9,'/Applications/Other.app/Contents/MacOS/Other')
        with self.assertRaises(RuntimeError):backend.newline()
        self.assertEqual(backend.events,[])
    def test_cancelled_remote_session_sends_no_newline(self):
        backend=Receiver();stop=threading.Event();backend.begin_typing('b',TypingConfig(),stop);stop.set()
        backend.newline();self.assertEqual(backend.events,[])
    def test_failed_key_release_still_releases_modifier(self):
        backend=Receiver();backend.begin_typing('A',TypingConfig(),threading.Event())
        original=backend.physical_key_event
        def fail(code,down):
            if code==0 and not down:raise RuntimeError('transport failure')
            return original(code,down)
        backend.physical_key_event=fail
        with self.assertRaises(RuntimeError):backend.write('A')
        self.assertNotIn(56,backend._held_keys)
    def test_unknown_focus_rejects_before_sending_virtual_a(self):
        backend=Receiver();backend.front=None
        with self.assertRaises(RuntimeError):backend.begin_typing('b',TypingConfig(),threading.Event())
        self.assertEqual(backend.events,[])
    def test_cleanup_failure_is_an_error_not_success(self):
        import queue
        from engine import type_text
        backend=Receiver();backend.front=(9,'/Applications/TextEdit.app/Contents/MacOS/TextEdit')
        def fail():raise RuntimeError('cleanup failed')
        backend.end_typing=fail;events=queue.Queue()
        type_text('',TypingConfig(start_delay=0),backend,threading.Event(),events)
        self.assertEqual(list(events.queue)[-1],('error','cleanup failed'))
        self.assertNotIn('finished',[event[0] for event in events.queue])
