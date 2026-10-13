"""Verify SendInput in a native Win32 EDIT control owned by this process.

Using the actual Windows control avoids Tcl/Tk's WM_CHAR/WM_KEYDOWN
translation of surrogate pairs. All events are constrained to this target.
"""
import ctypes as C
import os
from pathlib import Path
import queue
import sys
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from platform_backend import WindowsBackend, WinPoint, bind

class Message(C.Structure):
    _fields_=[('hwnd',C.c_void_p),('message',C.c_uint32),('wparam',C.c_size_t),('lparam',C.c_ssize_t),('time',C.c_uint32),('point',WinPoint),('private',C.c_uint32)]

backend=WindowsBackend();user=C.WinDLL('user32',use_last_error=True);kernel=C.WinDLL('kernel32',use_last_error=True)
create=bind(user,'CreateWindowExW',C.c_void_p,C.c_uint32,C.c_wchar_p,C.c_wchar_p,C.c_uint32,C.c_int32,C.c_int32,C.c_int32,C.c_int32,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p)
module=bind(kernel,'GetModuleHandleW',C.c_void_p,C.c_wchar_p)
foreground=bind(user,'GetForegroundWindow',C.c_void_p)
activate=bind(user,'SetForegroundWindow',C.c_bool,C.c_void_p)
focus=bind(user,'SetFocus',C.c_void_p,C.c_void_p)
get_pid=bind(user,'GetWindowThreadProcessId',C.c_uint32,C.c_void_p,C.POINTER(C.c_uint32))
peek=bind(user,'PeekMessageW',C.c_bool,C.POINTER(Message),C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32)
translate=bind(user,'TranslateMessage',C.c_bool,C.POINTER(Message))
dispatch=bind(user,'DispatchMessageW',C.c_ssize_t,C.POINTER(Message))
text_length=bind(user,'GetWindowTextLengthW',C.c_int32,C.c_void_p)
get_text=bind(user,'GetWindowTextW',C.c_int32,C.c_void_p,C.c_wchar_p,C.c_int32)
destroy=bind(user,'DestroyWindow',C.c_bool,C.c_void_p)
# WS_VISIBLE | WS_OVERLAPPEDWINDOW | ES_MULTILINE | ES_AUTOVSCROLL
window=create(0,'EDIT','',0x10CF0044,120,120,640,280,None,None,module(None),None)
if not window:raise RuntimeError(f'Native EDIT creation failed: {C.get_last_error()}')
results=queue.Queue();escaped=threading.Event();without_listener='--without-listener' in sys.argv
if not without_listener:backend.listen_escape(escaped.set)
expected='İıŞşĞğÜüÖöÇç 🙂\nWindows native input'
def require_target():
    pid=C.c_uint32();get_pid(foreground(),C.byref(pid))
    if pid.value!=os.getpid():raise RuntimeError('Controlled native test lost foreground focus; input aborted')
def send():
    try:
        require_target()
        for char in expected.split('\n')[0]:require_target();backend.write(char);time.sleep(.05)
        require_target();backend.newline();time.sleep(.1)
        for char in expected.split('\n')[1]:require_target();backend.write(char);time.sleep(.05)
        backend.press(0x1B)
        before=backend.position();backend.micro_activity(False,threading.Event());time.sleep(.15);after=backend.position()
        if (before.x,before.y)!=(after.x,after.y):raise RuntimeError('Cursor did not return or user moved it')
        results.put(None)
    except Exception as exc:results.put(exc)

message=Message();started=False;result=None;finished=False;start=time.monotonic()
activate(window);focus(window)
try:
    while time.monotonic()-start<15:
        while peek(C.byref(message),None,0,0,1):translate(C.byref(message));dispatch(C.byref(message))
        if not started and time.monotonic()-start>.7:
            require_target();threading.Thread(target=send,daemon=True).start();started=True
        try:result=results.get_nowait();finished=True;break
        except queue.Empty:time.sleep(.005)
    if not finished:raise RuntimeError('Native Windows input timed out')
    if result:raise result
    # Drain queued WM_CHAR messages before inspecting the native control.
    while peek(C.byref(message),None,0,0,1):translate(C.byref(message));dispatch(C.byref(message))
    buffer=C.create_unicode_buffer(text_length(window)+1);get_text(window,buffer,len(buffer))
    actual=buffer.value.replace('\r\n','\n')
    assert actual==expected,(repr(actual),repr(expected))
    if not without_listener:assert escaped.wait(1),'Global ESC was not detected'
    print('Native Windows input PASS: Win32 EDIT, Turkish Unicode, emoji, Shift+Enter, cursor return'+(', global ESC' if not without_listener else ', listener-free control'))
finally:backend.close();destroy(window)
