import unittest
from tools.windows_isolated_ui import isolated
class API:
    def __init__(self):self.calls=[];self.current=10
    def input_name(self):return 'Default'
    def thread_desktop(self):return self.current
    def create(self):self.calls.append('create');return 20
    def bind_thread(self,desktop):self.calls.append(('bind',desktop));self.current=desktop
    def close(self,desktop):self.calls.append(('close',desktop))
class IsolationTests(unittest.TestCase):
    def test_test_thread_uses_private_desktop_without_changing_input_desktop(self):
        api=API();seen=[]
        isolated(api,lambda:seen.append(api.current))
        self.assertEqual(seen,[20]);self.assertEqual(api.current,10)
        self.assertEqual(api.calls,['create',('bind',20),('bind',10),('close',20)])
    def test_exception_restores_borrowed_thread_desktop_and_closes_only_owned_desktop(self):
        api=API()
        def fail():raise RuntimeError('UI test failed')
        with self.assertRaises(RuntimeError):isolated(api,fail)
        self.assertEqual(api.calls[-2:],[('bind',10),('close',20)])
    def test_bind_failure_does_not_start_any_gui(self):
        api=API();seen=[]
        def reject(desktop):raise OSError('Desktop unavailable')
        api.bind_thread=reject
        with self.assertRaises(OSError):isolated(api,lambda:seen.append(True))
        self.assertEqual(seen,[]);self.assertEqual(api.calls,['create',('close',20)])
