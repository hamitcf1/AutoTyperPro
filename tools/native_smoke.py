"""Opt-in native integration check: sends events only to its own test window."""
import os
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from platform_backend import MacBackend
from AppKit import NSApplication, NSWorkspace

backend=MacBackend(); backend.require_permission()
root=tk.Tk(); root.title('AutoTyper native integration test'); root.geometry('620x260')
tk.Label(root,text='Yerel giriş testi — yalnızca bu geçici pencereye yazılır.').pack(pady=12)
text=tk.Text(root,font=('Helvetica',18)); text.pack(fill='both',expand=True)
text.focus_set()
results=queue.Queue(); escaped=threading.Event(); failures=[]
root.report_callback_exception=lambda kind,error,traceback: failures.append(error)
backend.listen_escape(escaped.set)
expected='İıŞşĞğÜüÖöÇç 🙂\nikinci satır'
def send():
    try:
        front=NSWorkspace.sharedWorkspace().frontmostApplication()
        if front.processIdentifier()!=os.getpid(): raise RuntimeError(f'Test window is not foreground (self={os.getpid()}, front={front.processIdentifier()}, app={front.localizedName()}); aborting input')
        def check_focus():
            if NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()!=os.getpid():raise RuntimeError('Native test lost focus; input stopped')
        for char in 'İıŞşĞğÜüÖöÇç 🙂':
            check_focus()
            backend.write(char); time.sleep(.05)
        check_focus(); backend.newline(); time.sleep(.1)
        for char in 'ikinci satır':
            check_focus()
            backend.write(char); time.sleep(.05)
        check_focus(); backend.press(53)
        check_focus(); before=backend.position(); backend.micro_activity(False,threading.Event()); time.sleep(.15); after=backend.position()
        if abs(before.x-after.x)>.5 or abs(before.y-after.y)>.5: raise RuntimeError('Cursor did not return (or user moved it)')
        results.put(None)
    except Exception as exc: results.put(exc)
def activate():
    NSApplication.sharedApplication().setActivationPolicy_(0)
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    root.lift(); text.focus_force()
    root.after(1000,wait_for_focus)
def wait_for_focus():
    if NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()==os.getpid():
        threading.Thread(target=send,daemon=True).start()
    else: root.after(100,wait_for_focus)
def check():
    try: result=results.get_nowait()
    except queue.Empty: root.after(100,check); return
    actual=text.get('1.0','end-1c')
    backend.close(); root.destroy()
    if result: raise result
    assert actual==expected,(repr(actual),repr(expected))
    assert escaped.wait(1),'Global ESC did not fire'
    print('Native smoke PASS: Turkish Unicode, emoji, Shift+Enter, global ESC, bounded mouse excursion and return')
root.after(300,activate); root.after(500,check)
root.after(30000,lambda:(failures.append(RuntimeError('Native integration timeout')),backend.close(),root.destroy()))
root.mainloop()
if failures: raise failures[0]
