from localization import tr
"""Native macOS input adapter, with an optional pynput desktop fallback."""
import ctypes as C
from pathlib import Path
import subprocess
import sys
import threading
import time
from activity import perform_activity, xy
from engine import JigglerConfig
from native_keys import KeyChordMixin
from keycodes import MAC_MODIFIER_FLAGS

class Point(C.Structure):
    _fields_ = [('x', C.c_double), ('y', C.c_double)]

class Size(C.Structure):
    _fields_ = [('width', C.c_double), ('height', C.c_double)]

class Rect(C.Structure):
    _fields_ = [('origin', Point), ('size', Size)]

def bind(lib, name, result, *args):
    fn = getattr(lib, name)
    fn.restype = result
    fn.argtypes = args
    return fn

def wait_for_listener(listener, mac=False, timeout=2):
    """Bound startup and reject pynput's silent event-tap creation failure.

    pynput 1.8 signals _ready even when CGEventTapCreate fails; _loop is
    populated only after a functioning tap is installed. Inspect both.
    """
    deadline = time.monotonic() + timeout
    while listener.is_alive() and (not getattr(listener, '_ready', False)) and (time.monotonic() < deadline):
        time.sleep(0.01)
    if not listener.is_alive() or not getattr(listener, '_ready', False) or (mac and getattr(listener, '_loop', None) is None):
        listener.stop()
        raise RuntimeError(tr('ui.89d4b73e680f'))

class MacEscapeListener(threading.Thread):
    """Observe physical Escape codes without Carbon keyboard-layout APIs.

    New macOS versions require input-source queries on the main queue. ESC
    has a fixed virtual key code, so this listener never needs those queries.
    The tap only observes events and cannot suppress or modify user input.
    """

    def __init__(self, callback):
        super().__init__(name='AutoTyper Escape', daemon=True)
        self.callback = callback
        self._stop_event = threading.Event()
        self._ready = False
        self._loop = None
        self.running = False
        self.cg = C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        self.cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        callback_type = C.CFUNCTYPE(C.c_void_p, C.c_void_p, C.c_uint32, C.c_void_p, C.c_void_p)
        self._native_callback = callback_type(self.handle_event)
        self.create_tap = bind(self.cg, 'CGEventTapCreate', C.c_void_p, C.c_uint32, C.c_uint32, C.c_uint32, C.c_uint64, callback_type, C.c_void_p)
        self.enable = bind(self.cg, 'CGEventTapEnable', None, C.c_void_p, C.c_bool)
        self.keycode = bind(self.cg, 'CGEventGetIntegerValueField', C.c_int64, C.c_void_p, C.c_uint32)
        self.create_source = bind(self.cf, 'CFMachPortCreateRunLoopSource', C.c_void_p, C.c_void_p, C.c_void_p, C.c_long)
        self.current_loop = bind(self.cf, 'CFRunLoopGetCurrent', C.c_void_p)
        self.add_source = bind(self.cf, 'CFRunLoopAddSource', None, C.c_void_p, C.c_void_p, C.c_void_p)
        self.remove_source = bind(self.cf, 'CFRunLoopRemoveSource', None, C.c_void_p, C.c_void_p, C.c_void_p)
        self.run_mode = bind(self.cf, 'CFRunLoopRunInMode', C.c_int32, C.c_void_p, C.c_double, C.c_bool)
        self.invalidate = bind(self.cf, 'CFMachPortInvalidate', None, C.c_void_p)
        self.release = bind(self.cf, 'CFRelease', None, C.c_void_p)
        self.mode = C.c_void_p.in_dll(self.cf, 'kCFRunLoopDefaultMode').value
        self.event_mask = 1 << 10
        self.tap = None

    def handle_event(self, proxy, kind, event, context):
        if self._stop_event.is_set():
            return event
        if kind in (4294967294, 4294967295):
            self.enable(self.tap, True)
        elif kind == 10 and self.keycode(event, 9) == 53:
            self.callback()
        return event

    def run(self):
        source = None
        try:
            self.tap = self.create_tap(1, 0, 1, self.event_mask, self._native_callback, None)
            if not self.tap:
                return
            source = self.create_source(None, self.tap, 0)
            if not source:
                return
            self._loop = self.current_loop()
            self.add_source(self._loop, source, self.mode)
            self.enable(self.tap, True)
            self.running = True
            self._ready = True
            while not self._stop_event.is_set():
                if self.run_mode(self.mode, 0.2, False) in (1, 2):
                    break
        finally:
            self.running = False
            self._ready = True
            if source:
                self.remove_source(self._loop, source, self.mode)
                self.release(source)
            self._loop = None
            if self.tap:
                self.invalidate(self.tap)
                self.release(self.tap)
                self.tap = None

    def stop(self):
        self._stop_event.set()

class MacBackend(KeyChordMixin):
    native_platform = 'darwin'

    def __init__(self):
        self.cg = C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        self.cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.ax = C.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        self.trusted = bind(self.ax, 'AXIsProcessTrusted', C.c_bool)
        self.post_allowed = bind(self.cg, 'CGPreflightPostEventAccess', C.c_bool)
        self.trusted_options = bind(self.ax, 'AXIsProcessTrustedWithOptions', C.c_bool, C.c_void_p)
        self.prompt_key = C.c_void_p.in_dll(self.ax, 'kAXTrustedCheckOptionPrompt').value
        self.cf_true = C.c_void_p.in_dll(self.cf, 'kCFBooleanTrue').value
        self.dictionary = bind(self.cf, 'CFDictionaryCreate', C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p), C.POINTER(C.c_void_p), C.c_long, C.c_void_p, C.c_void_p)
        self.release = bind(self.cf, 'CFRelease', None, C.c_void_p)
        self.key = bind(self.cg, 'CGEventCreateKeyboardEvent', C.c_void_p, C.c_void_p, C.c_uint16, C.c_bool)
        self.unicode = bind(self.cg, 'CGEventKeyboardSetUnicodeString', None, C.c_void_p, C.c_ulong, C.POINTER(C.c_uint16))
        self.flags = bind(self.cg, 'CGEventSetFlags', None, C.c_void_p, C.c_uint64)
        self.post = bind(self.cg, 'CGEventPost', None, C.c_uint32, C.c_void_p)
        self.event = bind(self.cg, 'CGEventCreate', C.c_void_p, C.c_void_p)
        self.location = bind(self.cg, 'CGEventGetLocation', Point, C.c_void_p)
        self.mouse = bind(self.cg, 'CGEventCreateMouseEvent', C.c_void_p, C.c_void_p, C.c_uint32, Point, C.c_uint32)
        self.idle = bind(self.cg, 'CGEventSourceSecondsSinceLastEventType', C.c_double, C.c_int32, C.c_uint32)
        self.displays = bind(self.cg, 'CGGetDisplaysWithPoint', C.c_int32, Point, C.c_uint32, C.POINTER(C.c_uint32), C.POINTER(C.c_uint32))
        self.bounds = bind(self.cg, 'CGDisplayBounds', Rect, C.c_uint32)
        self.lock = threading.RLock()
        self.listener = None

    def allowed(self):
        return bool(self.trusted() or self.post_allowed())

    def request_permission(self):
        """Register this process with macOS; only call after an explicit user action.

        The OS prompt is asynchronous. Its return value never implies a grant.
        Static CF constants remain alive while the non-retaining dictionary is used.
        """
        if self.allowed():
            return True
        keys = (C.c_void_p * 1)(self.prompt_key)
        values = (C.c_void_p * 1)(self.cf_true)
        options = self.dictionary(None, keys, values, 1, None, None)
        if not options:
            raise RuntimeError(tr('ui.11b2f26be6ff'))
        try:
            return bool(self.trusted_options(options))
        finally:
            self.release(options)

    def require_permission(self):
        if not self.allowed():
            raise PermissionError(tr('ui.b0bfaae8ac51'))

    def send(self, event):
        if not event:
            raise RuntimeError(tr('ui.79ad27e4fc1d'))
        try:
            self.post(0, event)
        finally:
            self.release(event)

    def write(self, text):
        self.require_permission()
        data = text.encode('utf-16-le')
        units = (C.c_uint16 * (len(data) // 2)).from_buffer_copy(data)
        with self.lock:
            for down in (True, False):
                event = self.key(None, 0, down)
                if not event:
                    raise RuntimeError(tr('ui.06d02628d4f8'))
                self.flags(event, 0)
                self.unicode(event, len(units), units)
                self.send(event)

    def press(self, code, flags=0):
        if flags:
            self.key_chord('enter',('shift',),threading.Event());return
        try:self.physical_key_event(code,True)
        finally:self.physical_key_event(code,False)

    def newline(self):
        self.press(36, 1 << 17)

    def position(self):
        event = self.event(None)
        if not event:
            raise RuntimeError(tr('ui.24e536bac916'))
        try:
            return self.location(event)
        finally:
            self.release(event)

    def idle_seconds(self):
        return self.idle(1, 4294967295)

    def screen_bounds(self, origin):
        origin=Point(*xy(origin)); display=C.c_uint32();count=C.c_uint32()
        if self.displays(origin,1,C.byref(display),C.byref(count)) != 0 or not count.value:
            raise RuntimeError(tr('input.no_display'))
        bounds=self.bounds(display.value)
        return bounds.origin.x,bounds.origin.y,bounds.origin.x+bounds.size.width,bounds.origin.y+bounds.size.height

    def move_to(self, point):
        self.require_permission()
        self.send(self.mouse(None,5,Point(*xy(point)),0))

    def physical_key_event(self,code,down):
        self.require_permission()
        with self.lock:
            if not hasattr(self,'_held_keys'):self._held_keys=set()
            if down:self._held_keys.add(code)
            event=self.key(None,code,down)
            if not event:raise RuntimeError(tr('input.key_event'))
            flags=0
            for held in self._held_keys:
                if down or held!=code:flags |= MAC_MODIFIER_FLAGS.get(held,0)
            self.flags(event,flags);self.send(event)
            if not down:self._held_keys.discard(code)

    def listen_events(self,callback,capture):
        from event_capture import listen_mac
        self.require_permission();listener=listen_mac(callback,capture)
        if not hasattr(self,'capture_listeners'):self.capture_listeners=[]
        self.capture_listeners.append(listener);return listener

    def display_layout(self):
        active=bind(self.cg,'CGGetActiveDisplayList',C.c_int32,C.c_uint32,C.POINTER(C.c_uint32),C.POINTER(C.c_uint32))
        main=bind(self.cg,'CGMainDisplayID',C.c_uint32)()
        displays=(C.c_uint32*16)();count=C.c_uint32()
        if active(16,displays,C.byref(count)) != 0 or not count.value:raise RuntimeError(tr('input.no_display'))
        result=[]
        for identity in sorted(displays[:count.value],key=lambda value:value!=main):
            rect=self.bounds(identity)
            result.append({'left':rect.origin.x,'top':rect.origin.y,'width':rect.size.width,'height':rect.size.height})
        return result

    def button_event(self,button,down,point=None):
        self.require_permission()
        codes={'left':(1,2,0),'right':(3,4,1),'middle':(25,26,2),'x1':(25,26,3),'x2':(25,26,4)}
        with self.lock:
            if not hasattr(self,'_held_buttons'):self._held_buttons=set()
            if down:self._held_buttons.add(button)
            if point is not None:self.move_to(point)
            position=Point(*xy(self.position()))
            before,after,index=codes[button]
            self.send(self.mouse(None,before if down else after,position,index))
            if not down:self._held_buttons.discard(button)

    def scroll_event(self,dx,dy):
        self.require_permission()
        create=bind(self.cg,'CGEventCreateScrollWheelEvent',C.c_void_p,C.c_void_p,C.c_uint32,C.c_uint32,C.c_int32,C.c_int32)
        with self.lock:self.send(create(None,1,2,round(dy),round(dx)))

    def micro_activity(self,config,stop):
        self.require_permission()
        if isinstance(config,bool):config=JigglerConfig(key='f18' if config else None)
        with self.lock:
            if getattr(self,'_activity_should_yield',lambda:False)():return False
            return perform_activity(self,config,stop)

    def listen_escape(self, callback):
        self.listener = MacEscapeListener(callback)
        self.listener.start()
        wait_for_listener(self.listener, mac=True)

    def escape_healthy(self):
        return bool(self.listener and self.listener.is_alive() and self.listener.running and (getattr(self.listener, '_loop', None) is not None))

    def close(self):
        for listener in getattr(self,'capture_listeners',()):listener.stop()
        if self.listener:
            self.listener.stop()

class DesktopBackend:

    def __init__(self):
        from pynput import keyboard, mouse
        self.keyboard_module = keyboard
        self.keyboard = keyboard.Controller()
        self.mouse = mouse.Controller()
        self.listener = None

    def allowed(self):
        return True

    def require_permission(self):
        pass

    def write(self, text):
        self.keyboard.type(text)

    def newline(self):
        with self.keyboard.pressed(self.keyboard_module.Key.shift):
            self.keyboard.press(self.keyboard_module.Key.enter)
            self.keyboard.release(self.keyboard_module.Key.enter)

    def listen_escape(self, callback):
        self.listener = self.keyboard_module.Listener(on_press=lambda key: callback() if key == self.keyboard_module.Key.esc else None)
        self.listener.start()
        wait_for_listener(self.listener)

    def escape_healthy(self):
        return bool(self.listener and self.listener.is_alive() and self.listener.running)

    def idle_seconds(self):
        raise RuntimeError(tr('ui.f98309cec1f8'))

    def close(self):
        for listener in getattr(self,'capture_listeners',()):listener.stop()
        if self.listener:
            self.listener.stop()

def create_backend():
    if sys.platform == 'darwin':
        return MacBackend()
    if sys.platform == 'win32':
        return WindowsBackend()
    return DesktopBackend()

def open_permissions():
    if sys.platform == 'darwin':
        subprocess.Popen(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])

def play_sound(name):
    path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'sounds' / f'{name}.wav'
    if not path.exists():
        return
    if sys.platform == 'darwin':
        subprocess.Popen(['/usr/bin/afplay', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == 'win32':
        import winsound
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)

def elapsed_idle(now_ms, last_ms):
    """GetTickCount/GetLastInputInfo use wrapping unsigned 32-bit ticks."""
    return (now_ms - last_ms & 4294967295) / 1000

class WinPoint(C.Structure):
    _fields_ = [('x', C.c_int32), ('y', C.c_int32)]

class WinRect(C.Structure):
    _fields_ = [('left', C.c_int32), ('top', C.c_int32), ('right', C.c_int32), ('bottom', C.c_int32)]

class MonitorInfo(C.Structure):
    _fields_ = [('size', C.c_uint32), ('monitor', WinRect), ('work', WinRect), ('flags', C.c_uint32)]

class LastInputInfo(C.Structure):
    _fields_ = [('size', C.c_uint32), ('time', C.c_uint32)]

class MouseInput(C.Structure):
    _fields_ = [('dx', C.c_int32), ('dy', C.c_int32), ('data', C.c_uint32), ('flags', C.c_uint32), ('time', C.c_uint32), ('extra', C.c_size_t)]

class KeyboardInput(C.Structure):
    _fields_ = [('vk', C.c_uint16), ('scan', C.c_uint16), ('flags', C.c_uint32), ('time', C.c_uint32), ('extra', C.c_size_t)]

class InputUnion(C.Union):
    _fields_ = [('mouse', MouseInput), ('keyboard', KeyboardInput)]

class Input(C.Structure):
    _fields_ = [('kind', C.c_uint32), ('payload', InputUnion)]

class WindowsBackend(KeyChordMixin, DesktopBackend):
    native_platform = 'win32'

    def __init__(self):
        super().__init__()
        user = C.WinDLL('user32', use_last_error=True)
        kernel = C.WinDLL('kernel32', use_last_error=True)
        self.last_input = bind(user, 'GetLastInputInfo', C.c_bool, C.POINTER(LastInputInfo))
        self.ticks = bind(kernel, 'GetTickCount', C.c_uint32)
        self.get_position = bind(user, 'GetCursorPos', C.c_bool, C.POINTER(WinPoint))
        self.monitor_at = bind(user, 'MonitorFromPoint', C.c_void_p, WinPoint, C.c_uint32)
        self.monitor_info = bind(user, 'GetMonitorInfoW', C.c_bool, C.c_void_p, C.POINTER(MonitorInfo))
        self.metric = bind(user, 'GetSystemMetrics', C.c_int32, C.c_int32)
        self.send_input = bind(user, 'SendInput', C.c_uint32, C.c_uint32, C.POINTER(Input), C.c_int32)
        self.scan_code = bind(user, 'MapVirtualKeyW', C.c_uint32, C.c_uint32, C.c_uint32)
        self.lock = threading.RLock()

    def keyboard_events(self, events):
        for event in events:
            if event.vk and (not event.flags & 4):
                event.scan = self.scan_code(event.vk, 0)
        inputs = (Input * len(events))(*(Input(1, InputUnion(keyboard=e)) for e in events))
        count = self.send_input(len(inputs), inputs, C.sizeof(Input))
        if count != len(inputs):
            releases = [KeyboardInput(e.vk, e.scan, 2, 0, 0) for e in events if e.vk and (not e.flags & 2)]
            if releases:
                cleanup = (Input * len(releases))(*(Input(1, InputUnion(keyboard=e)) for e in releases))
                self.send_input(len(cleanup), cleanup, C.sizeof(Input))
            raise RuntimeError(tr('ui.f1ab475ec465'))

    def write(self, text):
        data = text.encode('utf-16-le')
        units = (C.c_uint16 * (len(data) // 2)).from_buffer_copy(data)
        events = [KeyboardInput(0, unit, flag, 0, 0) for unit in units for flag in (4, 6)]
        with self.lock:
            self.keyboard_events(events)

    def newline(self):
        with self.lock:
            self.keyboard_events([KeyboardInput(16, 0, 0, 0, 0), KeyboardInput(13, 0, 0, 0, 0), KeyboardInput(13, 0, 2, 0, 0), KeyboardInput(16, 0, 2, 0, 0)])

    def press(self,code):
        try:self.physical_key_event(code,True)
        finally:self.physical_key_event(code,False)

    def idle_seconds(self):
        info = LastInputInfo(C.sizeof(LastInputInfo), 0)
        if not self.last_input(C.byref(info)):
            raise RuntimeError(tr('ui.193c48735b3d'))
        return elapsed_idle(self.ticks(), info.time)

    def position(self):
        point = WinPoint()
        if not self.get_position(C.byref(point)):
            raise RuntimeError(tr('ui.24e536bac916'))
        return point

    def move_to(self, point):
        point=WinPoint(*map(round,xy(point)))
        left, top, width, height = (self.metric(i) for i in (76, 77, 78, 79))
        if width <= 1 or height <= 1:
            raise RuntimeError(tr('ui.fd9930971d87'))
        dx = round((point.x - left) * 65535 / (width - 1))
        dy = round((point.y - top) * 65535 / (height - 1))
        event = Input(0, InputUnion(mouse=MouseInput(dx, dy, 0, 49153, 0, 0)))
        if self.send_input(1, C.byref(event), C.sizeof(Input)) != 1:
            raise RuntimeError(tr('ui.aca15376aca9'))

    def screen_bounds(self,point):
        point=WinPoint(*map(round,xy(point)))
        info=MonitorInfo();info.size=C.sizeof(info)
        if not self.monitor_info(self.monitor_at(point,2),C.byref(info)):
            raise RuntimeError(tr('input.no_display'))
        return info.monitor.left,info.monitor.top,info.monitor.right,info.monitor.bottom

    def physical_key_event(self,code,down):
        with self.lock:
            if not hasattr(self,'_held_keys'):self._held_keys=set()
            if down:self._held_keys.add(code)
            extended=1 if code in (0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x2D,0x2E,0x5B,0x5C,0x6F,0x90,0xA3,0xA5) else 0
            self.keyboard_events([KeyboardInput(code,0,extended | (0 if down else 2),0,0)])
            if not down:self._held_keys.discard(code)

    def listen_events(self,callback,capture):
        from event_capture import listen_windows
        listener=listen_windows(callback,capture)
        if not hasattr(self,'capture_listeners'):self.capture_listeners=[]
        self.capture_listeners.append(listener);return listener

    def display_layout(self):
        callback_type=C.WINFUNCTYPE(C.c_bool,C.c_void_p,C.c_void_p,C.POINTER(WinRect),C.c_ssize_t)
        enumerate_=bind(C.WinDLL('user32'),'EnumDisplayMonitors',C.c_bool,C.c_void_p,C.c_void_p,callback_type,C.c_ssize_t)
        result=[];failure=[]
        def callback(monitor,context,rect,data):
            info=MonitorInfo();info.size=C.sizeof(info)
            if not self.monitor_info(monitor,C.byref(info)):failure.append(True);return False
            r=info.monitor
            item={'left':r.left,'top':r.top,'width':r.right-r.left,'height':r.bottom-r.top}
            if info.flags & 1:result.insert(0,item)
            else:result.append(item)
            return True
        if not enumerate_(None,None,callback_type(callback),0) or failure or not result:raise RuntimeError(tr('input.no_display'))
        return result

    def button_event(self,button,down,point=None):
        flags={'left':(2,4,0),'right':(8,16,0),'middle':(32,64,0),'x1':(128,256,1),'x2':(128,256,2)}
        with self.lock:
            if not hasattr(self,'_held_buttons'):self._held_buttons=set()
            if down:self._held_buttons.add(button)
            if point is not None:self.move_to(point)
            before,after,value=flags[button]
            event=Input(0,InputUnion(mouse=MouseInput(0,0,value,before if down else after,0,0)))
            if self.send_input(1,C.byref(event),C.sizeof(Input))!=1:raise RuntimeError(tr('ui.aca15376aca9'))
            if not down:self._held_buttons.discard(button)

    def scroll_event(self,dx,dy):
        with self.lock:
            for amount,flag in ((dy,0x800),(dx,0x1000)):
                if not amount:continue
                event=Input(0,InputUnion(mouse=MouseInput(0,0,round(amount*120)&0xFFFFFFFF,flag,0,0)))
                if self.send_input(1,C.byref(event),C.sizeof(Input))!=1:raise RuntimeError(tr('ui.aca15376aca9'))

    def micro_activity(self,config,stop):
        if isinstance(config,bool):config=JigglerConfig(key='f18' if config else None)
        with self.lock:
            if getattr(self,'_activity_should_yield',lambda:False)():return False
            return perform_activity(self,config,stop)
