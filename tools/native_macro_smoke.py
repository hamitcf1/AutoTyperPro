"""Opt-in macOS record/replay check in a disposable, foreground-only target."""
import os
from pathlib import Path
import queue
import sys
import threading
import time
import tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from AppKit import NSApplication, NSWorkspace
from platform_backend import MacBackend
from macro_recorder import Recorder
from macros import play_macro

backend=MacBackend();backend.require_permission()
root=tk.Tk();root.title('AutoTyper native macro integration');root.geometry('620x280')
canvas=tk.Canvas(root,bg='#1D2420',highlightthickness=0,takefocus=True);canvas.pack(fill='both',expand=True)
canvas.create_text(310,100,text='Controlled macro test — no input outside this window',fill='#F0F3EF')
results=queue.Queue();failures=[];point=None
root.report_callback_exception=lambda kind,error,traceback:failures.append(error)
def foreground():
    if NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()!=os.getpid():raise RuntimeError('Controlled target lost focus; input aborted')
def work():
    recorder=None
    try:
        foreground();recorder=Recorder(backend,frozenset({'move','button','key','scroll'}),queue.Queue());recorder.start()
        foreground();backend.move_to(point);time.sleep(.08)
        foreground();backend.button_event('left',True,point);backend.button_event('left',False,point);time.sleep(.08)
        foreground();backend.press(79);time.sleep(.08)
        macro=recorder.stop();recorder=None
        assert any(e.kind=='button' for e in macro.events),'Native clicks were not recorded'
        assert any(e.kind=='key' and e.data['code']==79 for e in macro.events),'Native physical key was not recorded'
        recorder=Recorder(backend,frozenset({'key','button'}),queue.Queue());recorder.start()
        foreground();events=queue.Queue();play_macro(macro,backend,threading.Event(),events,start_delay=0,speed=2)
        time.sleep(.15);replayed=recorder.stop();recorder=None
        assert list(events.queue)[-1][0]=='macro_finished',list(events.queue)
        wanted=[(e.kind,e.data.get('code',e.data.get('button')),e.data['down']) for e in macro.events if e.kind in ('key','button')]
        actual=[(e.kind,e.data.get('code',e.data.get('button')),e.data['down']) for e in replayed.events if e.kind in ('key','button')]
        assert actual==wanted,(actual,wanted)
        assert not getattr(backend,'_held_keys',set()) and not getattr(backend,'_held_buttons',set())
        results.put(None)
    except Exception as exc:results.put(exc)
    finally:
        if recorder:
            try:recorder.stop()
            except Exception:pass
        backend.release_held_inputs()
def focus():
    global point
    NSApplication.sharedApplication().setActivationPolicy_(0)
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    root.lift();canvas.focus_force();point=(canvas.winfo_rootx()+200,canvas.winfo_rooty()+180)
    root.after(100,wait_for_focus)
def wait_for_focus():
    if NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()==os.getpid():threading.Thread(target=work,daemon=True).start()
    else:root.after(100,wait_for_focus)
def poll():
    try:result=results.get_nowait()
    except queue.Empty:root.after(100,poll);return
    if result:failures.append(result)
    root.destroy()
root.after(300,focus);root.after(400,poll)
root.after(30000,lambda:(failures.append(RuntimeError('Controlled target focus/integration timeout')),root.destroy()))
root.mainloop();backend.close()
if failures:raise failures[0]
print('Native macro PASS: raw key/click capture, validated replay, native observer agreement, held-input cleanup')
