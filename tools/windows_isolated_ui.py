"""Opt-in Windows UI tests on an invisible, temporary Win32 desktop.

Never calls SwitchDesktop, sends native input, or runs the shipped app.
https://learn.microsoft.com/en-us/windows/win32/winstation/thread-connection-to-a-desktop
"""
import ctypes as C
from pathlib import Path
import sys
import uuid


def isolated(api,run):
    visible=api.input_name();original=api.thread_desktop();private=api.create();bound=False
    try:
        api.bind_thread(private);bound=True
        if api.input_name()!=visible:raise RuntimeError('Input desktop changed before test')
        run()
        if api.input_name()!=visible:raise RuntimeError('Input desktop changed during test')
    finally:
        try:
            if bound:api.bind_thread(original)
        finally:api.close(private)


class WindowsDesktopAPI:
    def __init__(self):
        user=C.WinDLL('user32',use_last_error=True);kernel=C.WinDLL('kernel32',use_last_error=True)
        def bind(lib,name,result,*args):
            function=getattr(lib,name);function.restype=result;function.argtypes=args;return function
        self.get_thread=bind(kernel,'GetCurrentThreadId',C.c_uint32)
        self.get_desktop=bind(user,'GetThreadDesktop',C.c_void_p,C.c_uint32)
        self.create_desktop=bind(user,'CreateDesktopW',C.c_void_p,C.c_wchar_p,C.c_wchar_p,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p)
        self.set_thread=bind(user,'SetThreadDesktop',C.c_int,C.c_void_p)
        self.close_desktop=bind(user,'CloseDesktop',C.c_int,C.c_void_p)
        self.open_input=bind(user,'OpenInputDesktop',C.c_void_p,C.c_uint32,C.c_int,C.c_uint32)
        self.info=bind(user,'GetUserObjectInformationW',C.c_int,C.c_void_p,C.c_int,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32))
    def input_name(self):
        desktop=self.open_input(0,False,1)
        if not desktop:raise C.WinError(C.get_last_error())
        try:
            buffer=C.create_unicode_buffer(256);length=C.c_uint32()
            if not self.info(desktop,2,buffer,C.sizeof(buffer),C.byref(length)):raise C.WinError(C.get_last_error())
            return buffer.value
        finally:self.close(desktop)
    def thread_desktop(self):
        value=self.get_desktop(self.get_thread())
        if not value:raise C.WinError(C.get_last_error())
        return value
    def create(self):
        # Read/write/enumerate/create-window/create-menu; no SWITCHDESKTOP.
        value=self.create_desktop('AutoTyperTest-'+uuid.uuid4().hex,None,None,0,0xC7,None)
        if not value:raise C.WinError(C.get_last_error())
        return value
    def bind_thread(self,desktop):
        if not self.set_thread(desktop):raise C.WinError(C.get_last_error())
    def close(self,desktop):
        if not self.close_desktop(desktop):raise C.WinError(C.get_last_error())


def run_test(test):
    # Imports and all Tk creation happen AFTER this thread is isolated.
    import runpy
    from unittest.mock import patch
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from tools.ui_fakes import FakeBackend,FakeDesktop
    import auto_typer
    def forbidden(*args,**kwargs):raise RuntimeError('External UI is forbidden in isolated tests')
    with patch('auto_typer.create_backend',FakeBackend),patch('platform_backend.create_backend',FakeBackend),patch('auto_typer.play_sound'),patch('platform_backend.play_sound'),patch('desktop_integration.create_driver',lambda *args:FakeDesktop()),patch('webbrowser.open',forbidden):
        runpy.run_path(str(root/'tools'/('ui_smoke.py' if test=='ui' else 'entrypoint_ui_smoke.py')),run_name='__main__')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--test',choices=['ui','entrypoint'],default='ui');args=parser.parse_args()
    if sys.platform!='win32':raise SystemExit('This isolated test runner is Windows-only; no UI was opened.')
    isolated(WindowsDesktopAPI(),lambda:run_test(args.test))
    print('Isolated UI test completed; input desktop unchanged. Native tray/input not tested.')
