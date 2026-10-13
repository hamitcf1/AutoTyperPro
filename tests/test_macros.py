import queue
import threading
import unittest

LAYOUT=[{'left':0,'top':0,'width':100,'height':100}]
def data(events,platform='darwin'):
    return {'platform':platform,'displays':LAYOUT,'events':events}
def event(time,kind,**values):return {'time':time,'kind':kind,'data':values}

class MacroTests(unittest.TestCase):
    def test_invalid_macro_events_rejected_before_playback(self):
        from macros import validate_macro
        cases=[
            [event(-1,'move',x=2,y=2)], [event(301,'move',x=2,y=2)],
            [event(2,'move',x=2,y=2),event(1,'move',x=3,y=3)],
            [event(0,'move',x=100,y=20)], [event(0,'move',x=float('nan'),y=2)],
            [event(0,'key',code=0,down=True)], [event(0,'key',code=53,down=True),event(1,'key',code=53,down=False)],
            [event(0,'unknown')], [event(0,'button',button='left',down=False,x=5,y=5)],
        ]
        for events in cases:
            with self.subTest(events=events),self.assertRaises(ValueError):validate_macro(data(events))
        with self.assertRaises(ValueError):validate_macro(data([event(0,'move',x=1,y=1)]*10001))
    def test_cancel_releases_pressed_keys(self):
        from macros import validate_macro,play_macro
        stop=threading.Event()
        class Backend:
            native_platform='darwin'
            def __init__(self):self.keys=[];self.released=False
            def display_layout(self):return LAYOUT
            def physical_key_event(self,code,down):self.keys.append((code,down));stop.set()
            def release_held_inputs(self):self.released=True
        backend=Backend();events=queue.Queue()
        macro=validate_macro(data([event(0,'key',code=56,down=True),event(1,'key',code=56,down=False)]))
        play_macro(macro,backend,stop,events,start_delay=0)
        self.assertEqual(backend.keys,[(56,True)])
        self.assertTrue(backend.released)
        self.assertEqual(events.get()[0],'macro_started')
        self.assertEqual(events.get()[0],'macro_progress')
        self.assertEqual(events.get()[0],'macro_stopped')
    def test_display_and_platform_mismatch_rejected(self):
        from macros import validate_macro,play_macro
        class Backend:
            native_platform='win32'
            def display_layout(self):return [{'left':0,'top':0,'width':200,'height':200}]
            def release_held_inputs(self):pass
        for events in ([event(0,'move',x=50,y=50)], [event(0,'key',code=0,down=True),event(.1,'key',code=0,down=False)]):
            queue_=queue.Queue();play_macro(validate_macro(data(events)),Backend(),threading.Event(),queue_,start_delay=0)
            self.assertEqual(queue_.get()[0],'macro_error')
    def test_invalid_uuid_types_rejected_without_store_mutation(self):
        from macros import MacroStore, validate_macro
        from pathlib import Path
        import json, tempfile
        with tempfile.TemporaryDirectory() as directory:
            store=MacroStore(Path(directory)/'macros')
            identity=store.save('Original',validate_macro(data([event(0,'move',x=1,y=1)])))
            before=(store.directory/(identity+'.json')).read_bytes()
            source=Path(directory)/'invalid.json'
            for bad in ([],{},None,True,3):
                source.write_text(json.dumps({'schema':1,'id':bad,'name':'Invalid','macro':data([event(0,'move',x=1,y=1)])}))
                with self.assertRaises(ValueError):store.import_file(source)
                self.assertEqual((store.directory/(identity+'.json')).read_bytes(),before)
            (store.directory/'corrupted.json').write_text(source.read_text())
            self.assertEqual([item['id'] for item in store.list()],[identity])
            self.assertTrue((store.directory/'corrupted.json').exists())
    def test_explicit_remapping_and_repeats(self):
        from macros import validate_macro,play_macro
        class Backend:
            native_platform='win32'
            def __init__(self):self.moves=[]
            def display_layout(self):return [{'left':100,'top':100,'width':200,'height':200}]
            def move_to(self,p):self.moves.append(p)
            def release_held_inputs(self):pass
        backend=Backend();q=queue.Queue()
        play_macro(validate_macro(data([event(0,'move',x=50,y=50)])),backend,threading.Event(),q,start_delay=0,repeats=2,fit_to_primary=True)
        self.assertEqual(backend.moves,[(200,200),(200,200)])
        self.assertEqual(list(q.queue)[-1][0],'macro_finished')
