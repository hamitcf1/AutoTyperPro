"""Queue-only desktop commands; platform UI is isolated from automation widgets."""
import sys
from localization import tr
COMMANDS=frozenset(('open','typing','activity','macros','start_activity','stop_activity','stop_all','settings','about','report','quit'))

def create_driver(icon_path,enqueue):
    if sys.platform=='darwin':
        from desktop_macos import MacDesktop
        return MacDesktop(icon_path,enqueue)
    if sys.platform=='win32':
        from desktop_windows import WindowsDesktop
        return WindowsDesktop(icon_path,enqueue)
    raise RuntimeError('Desktop quick access requires macOS or Windows')

class DesktopIntegration:
    def __init__(self,events,icon_path,driver=None):
        self.events=events;self.icon_path=icon_path;self.driver=driver;self.notifications_enabled=False;self._alive=False;self._last=None
    @property
    def ready(self):return self._alive and self.driver is not None and self.driver.ready
    def enqueue(self,command):
        if self._alive and command in COMMANDS:self.events.put(command)
    def start(self):
        try:
            if self.driver is None:self.driver=create_driver(self.icon_path,self.enqueue)
            self._alive=bool(self.driver.start());return self._alive
        except Exception:
            self._alive=False;return False
    def update(self,status,active=False):
        labels={command:tr('desktop.'+command) for command in ('open','typing','activity','macros','stop_all','settings','about','report','quit')}
        labels['stop_activity' if active else 'start_activity']=tr('desktop.stop_activity' if active else 'desktop.start_activity')
        signature=(status,tuple(labels.items()))
        if self.ready and signature!=self._last:
            try:self.driver.update(status,labels);self._last=signature
            except Exception:pass
    def request_notifications(self):
        def finished(granted):
            if self._alive:self.events.put(('notification_permission',bool(granted)))
        try:
            if not self.ready:return finished(False)
            self.driver.request_notifications(finished)
        except Exception:finished(False)
    def notify(self,title,message):
        if not self.ready or not self.notifications_enabled:return False
        try:return bool(self.driver.notify(title,message))
        except Exception:return False
    def stop(self):
        if not self._alive:return
        self._alive=False
        try:self.driver.stop()
        except Exception:pass
