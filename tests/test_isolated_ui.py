import unittest
from types import SimpleNamespace
from tools.windows_isolated_ui import isolated,WindowsDesktopAPI
class API:
    def __init__(self):self.calls=[];self.original_thread=10
    def input_name(self):return 'Default'
    def create(self):self.calls.append('create');return (20,'PrivateTest')
    def close(self,desktop):self.calls.append(('close',desktop))
class IsolationTests(unittest.TestCase):
    def test_child_receives_private_desktop_and_parent_binding_is_untouched(self):
        api=API();seen=[]
        isolated(api,lambda private:seen.append(private))
        self.assertEqual(seen,[(20,'PrivateTest')]);self.assertEqual(api.original_thread,10)
        self.assertEqual(api.calls,['create',('close',(20,'PrivateTest'))])
    def test_failed_child_is_closed_before_private_desktop_is_closed(self):
        api=API()
        def fail(private):api.calls.append('child_closed');raise RuntimeError('UI test failed')
        with self.assertRaisesRegex(RuntimeError,'UI test failed'):isolated(api,fail)
        self.assertEqual(api.calls,['create','child_closed',('close',(20,'PrivateTest'))])
    def test_create_failure_starts_no_test(self):
        api=API();seen=[]
        def reject():raise OSError('Desktop unavailable')
        api.create=reject
        with self.assertRaises(OSError):isolated(api,lambda private:seen.append(True))
        self.assertEqual(seen,[])
    def test_timeout_terminates_only_created_child_and_closes_its_handles(self):
        api=WindowsDesktopAPI.__new__(WindowsDesktopAPI);closed=[];terminated=[];startup=[]
        def create(app,command,pa,ta,inherit,flags,env,cwd,info,process):
            startup.append((info._obj.lpDesktop,flags,inherit))
            process._obj.hProcess=21;process._obj.hThread=22;return True
        api.create_process=create;states=iter((258,0));api.wait=lambda *args:next(states);api.terminate=lambda handle,code:terminated.append(handle) or True
        api.close_handle=closed.append
        with self.assertRaises(TimeoutError):api.run('PrivateTest',['python','test.py'],1)
        self.assertEqual(startup,[('PrivateTest',0x08000000,False)])
        self.assertEqual(terminated,[21]);self.assertEqual(set(closed),{21,22})
    def test_direct_child_cannot_open_ui_on_visible_desktop(self):
        from tools.windows_isolated_ui import validate_child
        name='AutoTyperTest-'+'a'*32
        api=SimpleNamespace(thread_name=lambda:'Default',input_name=lambda:'Default')
        with self.assertRaises(RuntimeError):validate_child(api,name)
        api.thread_name=lambda:name;api.input_name=lambda:name
        with self.assertRaises(RuntimeError):validate_child(api,name)
        api.input_name=lambda:'Default';validate_child(api,name)
    def test_cleanup_error_preserves_the_original_test_failure(self):
        api=API()
        def close(private):raise OSError('cleanup failed')
        api.close=close
        def fail(private):raise RuntimeError('original test failure')
        with self.assertRaisesRegex(RuntimeError,'original test failure') as result:isolated(api,fail)
        self.assertIn('cleanup failed',result.exception.__notes__[0])
    def test_direct_test_function_refuses_visible_mac_ui(self):
        from tools.windows_isolated_ui import run_test
        from unittest.mock import patch
        with patch('sys.platform','darwin'),patch('runpy.run_path') as run:
            with self.assertRaises(RuntimeError):run_test('ui')
            run.assert_not_called()
