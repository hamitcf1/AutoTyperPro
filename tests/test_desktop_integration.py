import queue
import unittest

class Driver:
    ready=True
    def __init__(self):self.stops=0;self.notifications=[]
    def start(self):return True
    def update(self,status,labels):self.status=status
    def notify(self,title,message):self.notifications.append((title,message));return True
    def stop(self):self.stops+=1;self.ready=False

class DesktopTests(unittest.TestCase):
    def test_native_actions_queue_and_stop_blocks_late_callbacks(self):
        from desktop_integration import DesktopIntegration
        events=queue.Queue();driver=Driver();desktop=DesktopIntegration(events,None,driver=driver)
        self.assertTrue(desktop.start())
        desktop.enqueue('stop_all');self.assertEqual(events.get_nowait(),'stop_all')
        desktop.enqueue('invalid');self.assertTrue(events.empty())
        desktop.stop();desktop.stop();self.assertEqual(driver.stops,1)
        desktop.enqueue('start_activity');self.assertTrue(events.empty());self.assertFalse(desktop.ready)
    def test_unavailable_native_surface_and_notification_do_not_raise(self):
        from desktop_integration import DesktopIntegration
        driver=Driver();driver.start=lambda: (_ for _ in ()).throw(RuntimeError('unavailable'))
        desktop=DesktopIntegration(queue.Queue(),None,driver=driver)
        self.assertFalse(desktop.start());self.assertFalse(desktop.ready)
        self.assertFalse(desktop.notify('Done','Finished'))
    def test_notifications_are_optional_and_fail_closed(self):
        from desktop_integration import DesktopIntegration
        driver=Driver();desktop=DesktopIntegration(queue.Queue(),None,driver=driver);desktop.start()
        self.assertFalse(desktop.notify('Done','Finished'));self.assertEqual(driver.notifications,[])
        desktop.notifications_enabled=True;self.assertTrue(desktop.notify('Done','Finished'))
        driver.notify=lambda *args:(_ for _ in ()).throw(RuntimeError('denied'))
        self.assertFalse(desktop.notify('Done','Finished'))

class WindowsMenuTests(unittest.TestCase):
    def test_menu_callback_is_accepted_by_native_library(self):
        import importlib.util
        if importlib.util.find_spec('pystray') is None:self.skipTest('Windows menu library not installed')
        from pystray import MenuItem
        from desktop_windows import menu_action
        values=[]
        item=MenuItem('Quit',menu_action('quit',values.append));item(None)
        self.assertEqual(values,['quit'])
