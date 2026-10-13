"""Opt-in Windows macro check in a disposable native Win32 target."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import queue
import sys
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from platform_backend import WindowsBackend
from macro_recorder import Recorder
from macros import play_macro

user=C.WinDLL('user32',use_last_error=True)
def bind(name,result,*args):
    fn=getattr(user,name);fn.restype=result;fn.argtypes=args;return fn
create=bind('CreateWindowExW',W.HWND,W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p)
show=bind('ShowWindow',W.BOOL,W.HWND,C.c_int);focus=bind('SetForegroundWindow',W.BOOL,W.HWND)
foreground=bind('GetForegroundWindow',W.HWND);pid=bind('GetWindowThreadProcessId',W.DWORD,W.HWND,C.POINTER(W.DWORD))
rect=bind('GetWindowRect',W.BOOL,W.HWND,C.POINTER(W.RECT));destroy=bind('DestroyWindow',W.BOOL,W.HWND)
peek=bind('PeekMessageW',W.BOOL,C.POINTER(W.MSG),W.HWND,W.UINT,W.UINT,W.UINT)
translate=bind('TranslateMessage',W.BOOL,C.POINTER(W.MSG));dispatch=bind('DispatchMessageW',C.c_ssize_t,C.POINTER(W.MSG))
window=create(0,'STATIC','AutoTyper controlled macro target',0x10CF0000,100,100,640,320,None,None,None,None)
if not window:raise C.WinError(C.get_last_error())
show(window,5);focus(window)
backend=WindowsBackend();results=queue.Queue();stop=threading.Event();escaped=threading.Event()
backend.listen_escape(escaped.set)
bounds=W.RECT();rect(window,C.byref(bounds));point=(bounds.left+180,bounds.top+170)
def own_focus():
    current=W.DWORD();pid(foreground(),C.byref(current))
    if current.value!=os.getpid():raise RuntimeError('Controlled target lost focus; input aborted')
def wait_events(recorder):
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        with recorder.lock:
            if any(e.kind=='key' and not e.data['down'] for e in recorder.recorded):return
        time.sleep(.02)
    raise RuntimeError('Native input recorder did not receive the expected key')
def send():
    recorder=None
    try:
        time.sleep(.3);own_focus()
        recorder=Recorder(backend,frozenset({'key','button','move'}),queue.Queue());recorder.start()
        own_focus();backend.button_event('left',True,point);backend.button_event('left',False,point)
        own_focus();backend.press(0x81);wait_events(recorder)
        macro=recorder.stop();recorder=None
        assert any(e.kind=='button' for e in macro.events)
        recorder=Recorder(backend,frozenset({'key','button'}),queue.Queue());recorder.start()
        own_focus();events=queue.Queue();play_macro(macro,backend,stop,events,start_delay=0,speed=2)
        wait_events(recorder);replayed=recorder.stop();recorder=None
        wanted=[(e.kind,e.data.get('code',e.data.get('button')),e.data['down']) for e in macro.events if e.kind in ('key','button')]
        actual=[(e.kind,e.data.get('code',e.data.get('button')),e.data['down']) for e in replayed.events if e.kind in ('key','button')]
        assert actual==wanted,(actual,wanted)
        assert list(events.queue)[-1][0]=='macro_finished'
        assert not getattr(backend,'_held_keys',set()) and not getattr(backend,'_held_buttons',set())
        own_focus();backend.press(0x1B);assert escaped.wait(2),'Global Escape not delivered'
        results.put(None)
    except Exception as exc:results.put(exc)
    finally:
        if recorder:
            try:recorder.stop()
            except Exception:pass
        backend.release_held_inputs()
thread=threading.Thread(target=send,daemon=True);thread.start();message=W.MSG();deadline=time.monotonic()+20
try:
    while time.monotonic()<deadline:
        while peek(C.byref(message),None,0,0,1):translate(C.byref(message));dispatch(C.byref(message))
        if not results.empty():
            error=results.get()
            if error:raise error
            print('Windows macro PASS: native record/replay, observer agreement, held-input cleanup, Escape')
            break
        time.sleep(.01)
    else:raise RuntimeError('Native macro integration timeout')
finally:
    stop.set();backend.close();thread.join(2);destroy(window)
