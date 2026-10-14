"""Windows shell taskbar identity and notification-area menu."""
import ctypes
import threading

def menu_action(command,enqueue):
    def action(icon,item):enqueue(command)
    return action

class WindowsDesktop:
    def __init__(self,icon_path,enqueue):
        import pystray
        from PIL import Image
        self.module=pystray;self.enqueue=enqueue;self.ready=False;self.closed=threading.Event()
        with Image.open(icon_path) as image:icon=image.copy()
        self.icon=pystray.Icon('AutoTyperPro',icon,'AutoTyper Pro')
    def start(self):
        def setup(icon):
            if not self.closed.is_set():icon.visible=True;self.ready=True
        self.icon.run_detached(setup);return True
    def update(self,status,labels):
        module=self.module
        items=[module.MenuItem('AutoTyper Pro · '+status,lambda icon,item:None,enabled=False),module.Menu.SEPARATOR]
        for command,label in labels.items():
            items.append(module.MenuItem(label,menu_action(command,self.enqueue),default=command=='open'))
        self.icon.menu=module.Menu(*items);self.icon.title='AutoTyper Pro · '+status;self.icon.update_menu()
    def request_notifications(self,callback):callback(True)
    def notify(self,title,message):self.icon.notify(message,title);return True
    def stop(self):
        self.closed.set();self.ready=False;self.icon.visible=False;self.icon.stop()

def set_taskbar_identity():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('AetheriusCo.AutoTyperPro')
