"""Native event capture adapters. Never translate keys into characters on macOS."""
import ctypes as C
import time
from platform_backend import MacEscapeListener, Point, bind, wait_for_listener
from keycodes import MAC_MODIFIER_FLAGS

class MacEventListener(MacEscapeListener):
    def __init__(self,callback,capture):
        super().__init__(callback)
        self.capture=capture
        kinds={10,11,12}
        if 'move' in capture or 'button' in capture:kinds.update((5,6,7,27))
        if 'button' in capture:kinds.update((1,2,3,4,25,26))
        if 'scroll' in capture:kinds.add(22)
        self.event_mask=sum(1<<kind for kind in kinds)
        self.location=bind(self.cg,'CGEventGetLocation',Point,C.c_void_p)
        self.flags=bind(self.cg,'CGEventGetFlags',C.c_uint64,C.c_void_p)
    def handle_event(self,proxy,kind,event,context):
        if self._stop_event.is_set():return event
        if kind in (0xFFFFFFFE,0xFFFFFFFF):self.enable(self.tap,True);return event
        if kind in (10,11):self.callback('key',{'code':self.keycode(event,9),'down':kind==10})
        elif kind==12:
            code=self.keycode(event,9);flag=MAC_MODIFIER_FLAGS.get(code)
            if flag:self.callback('key',{'code':code,'down':bool(self.flags(event)&flag)})
        elif kind in (5,6,7,27):
            point=self.location(event);self.callback('move',{'x':point.x,'y':point.y})
        elif kind in (1,2,3,4,25,26):
            point=self.location(event)
            button=('left' if kind in (1,2) else 'right' if kind in (3,4) else {2:'middle',3:'x1',4:'x2'}.get(self.keycode(event,3)))
            if button:self.callback('button',{'button':button,'down':kind in (1,3,25),'x':point.x,'y':point.y})
        elif kind==22:self.callback('scroll',{'dx':self.keycode(event,12),'dy':self.keycode(event,11)})
        return event

class ListenerGroup:
    def __init__(self,listeners):self.listeners=listeners
    def stop(self):
        for listener in self.listeners:listener.stop()
    def is_alive(self):return any(listener.is_alive() for listener in self.listeners)
    def join(self,timeout=None):
        deadline=time.monotonic()+(timeout if timeout is not None else 2)
        for listener in self.listeners:listener.join(max(0,deadline-time.monotonic()))

def listen_mac(callback,capture):
    listener=MacEventListener(callback,capture);listener.start()
    wait_for_listener(listener,mac=True);return listener

def listen_windows(callback,capture):
    from pynput import keyboard, mouse
    def key_filter(message,data):
        if message in (0x100,0x101,0x104,0x105):
            callback('key',{'code':int(data.vkCode),'down':message in (0x100,0x104)})
        return False
    listeners=[keyboard.Listener(win32_event_filter=key_filter)]
    if set(capture)&{'move','button','scroll'}:
        listeners.append(mouse.Listener(
            on_move=lambda x,y:callback('move',{'x':x,'y':y}),
            on_click=lambda x,y,button,down:callback('button',{'x':x,'y':y,'button':button.name,'down':down}),
            on_scroll=lambda x,y,dx,dy:callback('scroll',{'dx':dx,'dy':dy})))
    group=ListenerGroup(listeners)
    try:
        for listener in listeners:listener.start();wait_for_listener(listener)
        return group
    except Exception:group.stop();group.join(2);raise
