"""Source UI tests in a separate process on an invisible Win32 desktop.
Never switches the input desktop or runs native input/tray/audio tests.
https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-startupinfow
"""
import ctypes as C
from pathlib import Path
import subprocess
import sys
import uuid

class StartupInfo(C.Structure):
    _fields_=[('cb',C.c_uint32),('lpReserved',C.c_wchar_p),('lpDesktop',C.c_wchar_p),('lpTitle',C.c_wchar_p),('dwX',C.c_uint32),('dwY',C.c_uint32),('dwXSize',C.c_uint32),('dwYSize',C.c_uint32),('dwXCountChars',C.c_uint32),('dwYCountChars',C.c_uint32),('dwFillAttribute',C.c_uint32),('dwFlags',C.c_uint32),('wShowWindow',C.c_uint16),('cbReserved2',C.c_uint16),('lpReserved2',C.c_void_p),('hStdInput',C.c_void_p),('hStdOutput',C.c_void_p),('hStdError',C.c_void_p)]
class ProcessInfo(C.Structure):
    _fields_=[('hProcess',C.c_void_p),('hThread',C.c_void_p),('dwProcessId',C.c_uint32),('dwThreadId',C.c_uint32)]

def isolated(api,run):
    visible=api.input_name();private=api.create();failure=None
    try:
        result=run(private)
        if api.input_name()!=visible:raise RuntimeError('Input desktop changed during test')
        return result
    except BaseException as exc:failure=exc;raise
    finally:
        try:api.close(private)
        except OSError as cleanup:
            if failure:failure.add_note('Private desktop cleanup: '+str(cleanup))
            else:raise

def validate_child(api,expected):
    import re
    if not expected or not re.fullmatch(r'AutoTyperTest-[0-9a-f]{32}',expected) or api.thread_name()!=expected or api.input_name()==expected:
        raise RuntimeError('UI child is not on its invisible test desktop; no UI was opened')

class WindowsDesktopAPI:
    def __init__(self):
        user=C.WinDLL('user32',use_last_error=True);kernel=C.WinDLL('kernel32',use_last_error=True)
        def bind(lib,name,result,*args):
            function=getattr(lib,name);function.restype=result;function.argtypes=args;return function
        self.current_thread=bind(kernel,'GetCurrentThreadId',C.c_uint32)
        self.get_thread_desktop=bind(user,'GetThreadDesktop',C.c_void_p,C.c_uint32)
        self.create_desktop=bind(user,'CreateDesktopW',C.c_void_p,C.c_wchar_p,C.c_wchar_p,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p)
        self.close_desktop=bind(user,'CloseDesktop',C.c_int,C.c_void_p)
        self.open_input=bind(user,'OpenInputDesktop',C.c_void_p,C.c_uint32,C.c_int,C.c_uint32)
        self.info=bind(user,'GetUserObjectInformationW',C.c_int,C.c_void_p,C.c_int,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32))
        self.create_process=bind(kernel,'CreateProcessW',C.c_int,C.c_wchar_p,C.c_wchar_p,C.c_void_p,C.c_void_p,C.c_int,C.c_uint32,C.c_void_p,C.c_wchar_p,C.POINTER(StartupInfo),C.POINTER(ProcessInfo))
        self.wait=bind(kernel,'WaitForSingleObject',C.c_uint32,C.c_void_p,C.c_uint32)
        self.exit_code=bind(kernel,'GetExitCodeProcess',C.c_int,C.c_void_p,C.POINTER(C.c_uint32))
        self.terminate=bind(kernel,'TerminateProcess',C.c_int,C.c_void_p,C.c_uint32)
        self.close_handle=bind(kernel,'CloseHandle',C.c_int,C.c_void_p)
    def thread_name(self):
        desktop=self.get_thread_desktop(self.current_thread())
        if not desktop:raise C.WinError(C.get_last_error())
        buffer=C.create_unicode_buffer(256);length=C.c_uint32()
        if not self.info(desktop,2,buffer,C.sizeof(buffer),C.byref(length)):raise C.WinError(C.get_last_error())
        return buffer.value  # GetThreadDesktop returns a borrowed handle.
    def input_name(self):
        desktop=self.open_input(0,False,1)
        if not desktop:raise C.WinError(C.get_last_error())
        try:
            buffer=C.create_unicode_buffer(256);length=C.c_uint32()
            if not self.info(desktop,2,buffer,C.sizeof(buffer),C.byref(length)):raise C.WinError(C.get_last_error())
            return buffer.value
        finally:self.close((desktop,None))
    def create(self):
        name='AutoTyperTest-'+uuid.uuid4().hex
        handle=self.create_desktop(name,None,None,0,0xC7,None)
        if not handle:raise C.WinError(C.get_last_error())
        return handle,name
    def close(self,desktop):
        if not self.close_desktop(desktop[0]):raise C.WinError(C.get_last_error())
    def run(self,desktop_name,arguments,timeout=45000):
        startup=StartupInfo();startup.cb=C.sizeof(startup);startup.lpDesktop=desktop_name
        process=ProcessInfo();command=C.create_unicode_buffer(subprocess.list2cmdline(arguments))
        if not self.create_process(arguments[0],command,None,None,False,0x08000000,None,str(Path(__file__).resolve().parents[1]),C.byref(startup),C.byref(process)):raise C.WinError(C.get_last_error())
        finished=False;failure=None
        try:
            status=self.wait(process.hProcess,timeout)
            if status==258:raise TimeoutError('Isolated UI test timed out')
            if status!=0:raise RuntimeError('Could not wait for isolated test process')
            finished=True;code=C.c_uint32()
            if not self.exit_code(process.hProcess,C.byref(code)):raise C.WinError(C.get_last_error())
            return code.value
        except BaseException as exc:failure=exc;raise
        finally:
            try:
                if not finished:
                    if not self.terminate(process.hProcess,1) or self.wait(process.hProcess,5000)!=0:
                        error=RuntimeError('Test child cleanup did not complete')
                        if failure:failure.add_note(str(error))
                        else:raise error
            finally:
                self.close_handle(process.hThread);self.close_handle(process.hProcess)

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
    import tempfile
    import traceback
    parser=argparse.ArgumentParser();parser.add_argument('--test',choices=['ui','entrypoint'],default='ui');parser.add_argument('--child',action='store_true');parser.add_argument('--log',type=Path);parser.add_argument('--desktop');args=parser.parse_args()
    if sys.platform!='win32':raise SystemExit('Windows-only test runner; no UI was opened.')
    if args.child:
        validate_child(WindowsDesktopAPI(),args.desktop)
        if args.log is None:raise SystemExit('Child log path required')
        with args.log.open('w',encoding='utf-8') as output:
            sys.stdout=sys.stderr=output
            try:run_test(args.test)
            except BaseException:traceback.print_exc();raise SystemExit(1)
    else:
        api=WindowsDesktopAPI()
        with tempfile.TemporaryDirectory(prefix='autotyper-isolated-') as directory:
            log=Path(directory)/'result.log'
            code=isolated(api,lambda private:api.run(private[1],[sys.executable,str(Path(__file__).resolve()),'--child','--desktop',private[1],'--test',args.test,'--log',str(log)]))
            if log.exists():print(log.read_text(encoding='utf-8'))
            if code:raise SystemExit(code)
        print('Isolated UI PASS: child exited, private desktop closed, input desktop unchanged. Native tray/input not tested.')
