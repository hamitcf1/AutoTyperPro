"""Opt-in Windows input check, constrained to its own foreground window."""
import ctypes as C
import os
from pathlib import Path
import queue
import sys
import threading
import time
import tkinter as tk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from platform_backend import WindowsBackend, bind

backend=WindowsBackend();user=C.WinDLL('user32',use_last_error=True)
ancestor=bind(user,'GetAncestor',C.c_void_p,C.c_void_p,C.c_uint32)
foreground=bind(user,'GetForegroundWindow',C.c_void_p)
activate=bind(user,'SetForegroundWindow',C.c_bool,C.c_void_p)
get_pid=bind(user,'GetWindowThreadProcessId',C.c_uint32,C.c_void_p,C.POINTER(C.c_uint32))
key_state=bind(user,'GetAsyncKeyState',C.c_int16,C.c_int32)
sys.stdout.reconfigure(encoding='utf-8')
root=tk.Tk();root.title('AutoTyper Windows native test');root.geometry('640x280')
text=tk.Text(root);text.pack(fill='both',expand=True)
text.bind('<KeyPress>',lambda e:print('Target key:',e.keysym,repr(e.char),e.state,flush=True))
results=queue.Queue();failures=[];escaped=threading.Event()
without_listener='--without-listener' in sys.argv
if not without_listener:backend.listen_escape(escaped.set)
root.report_callback_exception=lambda kind,error,traceback:failures.append(error)
expected='İıŞşĞğÜüÖöÇç 🙂\nWindows native input'
def require_target():
    pid=C.c_uint32();get_pid(foreground(),C.byref(pid))
    if pid.value!=os.getpid():raise RuntimeError(f'Test lost foreground focus: expected {os.getpid()}, got {pid.value}')
def modifiers():return {name:bool(key_state(code)&0x8000) for name,code in [('shift',0x10),('ctrl',0x11),('alt',0x12),('win',0x5B)]}
def send():
    try:
        pid=C.c_uint32();get_pid(foreground(),C.byref(pid))
        if pid.value!=os.getpid():
            results.put('skip');return
        print('Initial modifiers:',modifiers(),flush=True)
        for c in expected.split('\n')[0]:require_target();backend.write(c);time.sleep(.05)
        require_target();backend.newline();time.sleep(.15)
        print('After newline modifiers:',modifiers(),flush=True)
        for c in expected.split('\n')[1]:require_target();backend.write(c);time.sleep(.05)
        backend.press(0x1B)
        before=backend.position();backend.micro_activity(False,threading.Event());time.sleep(.15);after=backend.position()
        if (before.x,before.y)!=(after.x,after.y):raise RuntimeError('Cursor did not return or user moved it')
        results.put(None)
    except Exception as exc:results.put(exc)
def start():
    root.lift();activate(ancestor(root.winfo_id(),2));text.focus_force()
    root.after(500,lambda:threading.Thread(target=send,daemon=True).start())
def check():
    try:result=results.get_nowait()
    except queue.Empty:root.after(100,check);return
    actual=text.get('1.0','end-1c');backend.close();root.destroy()
    if result=='skip':print('Native Windows input SKIPPED: runner has no foreground interactive desktop');return
    if result:raise result
    assert actual==expected,(repr(actual),repr(expected))
    if not without_listener:assert escaped.wait(1),'Global ESC was not detected'
    print('Native Windows input PASS: Turkish Unicode, emoji, Shift+Enter, global ESC, cursor movement and return')
root.after(700,start);root.after(900,check)
root.after(15000,lambda:(failures.append(RuntimeError('Windows native test timeout')),backend.close(),root.destroy()))
root.mainloop()
if failures:raise failures[0]
