"""Native macOS input adapter, with an optional pynput desktop fallback."""
import ctypes as C
from pathlib import Path
import subprocess
import sys
import threading
import time


class Point(C.Structure):
    _fields_ = [('x', C.c_double), ('y', C.c_double)]

class Size(C.Structure):
    _fields_ = [('width', C.c_double), ('height', C.c_double)]

class Rect(C.Structure):
    _fields_ = [('origin', Point), ('size', Size)]


def bind(lib, name, result, *args):
    fn = getattr(lib, name); fn.restype = result; fn.argtypes = args; return fn


def wait_for_listener(listener, mac=False, timeout=2):
    """Bound startup and reject pynput's silent event-tap creation failure.

    pynput 1.8 signals _ready even when CGEventTapCreate fails; _loop is
    populated only after a functioning tap is installed. Inspect both.
    """
    deadline = time.monotonic() + timeout
    while listener.is_alive() and not getattr(listener, '_ready', False) and time.monotonic() < deadline:
        time.sleep(.01)
    if not listener.is_alive() or not getattr(listener, '_ready', False) or (mac and getattr(listener, '_loop', None) is None):
        listener.stop()
        raise RuntimeError('Global ESC izleyicisi hazır değil. Erişilebilirlik iznini kontrol edip yeniden deneyin.')


class MacBackend:
    def __init__(self):
        self.cg = C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        self.cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.ax = C.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        self.trusted = bind(self.ax, 'AXIsProcessTrusted', C.c_bool)
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
        self.lock = threading.Lock()
        self.listener = None

    def allowed(self): return bool(self.trusted())
    def require_permission(self):
        if not self.allowed(): raise PermissionError('Sistem Ayarları → Gizlilik ve Güvenlik → Erişilebilirlik bölümünde uygulamaya izin verin.')
    def send(self, event):
        if not event: raise RuntimeError('macOS giriş olayı oluşturulamadı.')
        try: self.post(0, event)
        finally: self.release(event)
    def write(self, text):
        self.require_permission()
        data = text.encode('utf-16-le'); units = (C.c_uint16 * (len(data)//2)).from_buffer_copy(data)
        with self.lock:
            for down in (True, False):
                event = self.key(None, 0, down)
                if not event: raise RuntimeError('Klavye olayı oluşturulamadı.')
                self.flags(event, 0)
                self.unicode(event, len(units), units); self.send(event)
    def press(self, code, flags=0):
        self.require_permission()
        with self.lock:
            for down in (True, False):
                event = self.key(None, code, down)
                if not event: raise RuntimeError('Klavye olayı oluşturulamadı.')
                self.flags(event, flags); self.send(event)
    def newline(self): self.press(36, 1 << 17)
    def position(self):
        event = self.event(None)
        if not event: raise RuntimeError('İmleç konumu okunamadı.')
        try: return self.location(event)
        finally: self.release(event)
    def idle_seconds(self): return self.idle(1, 0xFFFFFFFF)
    def micro_activity(self, f18, stop):
        self.require_permission()
        with self.lock:
            if stop.is_set(): return False
            origin = self.position(); display = C.c_uint32(); count = C.c_uint32()
            if self.displays(origin, 1, C.byref(display), C.byref(count)) != 0 or not count.value:
                raise RuntimeError('Etkin ekran bulunamadı.')
            bounds = self.bounds(display.value)
            x = min(origin.x + 1, bounds.origin.x + bounds.size.width - 1)
            if x == origin.x: x = max(bounds.origin.x, origin.x - 1)
            target = Point(x, origin.y)
            self.send(self.mouse(None, 5, target, 0))
            stop.wait(.08)
            current = self.position()
            if abs(current.x-target.x) < .25 and abs(current.y-target.y) < .25:
                self.send(self.mouse(None, 5, origin, 0))
        if f18 and not stop.is_set(): self.press(79)
        return True
    def listen_escape(self, callback):
        # pynput supplies a maintained event-tap lifecycle and teardown.
        from pynput import keyboard
        self.listener = keyboard.Listener(on_press=lambda key: callback() if key == keyboard.Key.esc else None)
        self.listener.start()
        wait_for_listener(self.listener, mac=True)
    def escape_healthy(self):
        return bool(self.listener and self.listener.is_alive() and self.listener.running and getattr(self.listener, '_loop', None) is not None)
    def close(self):
        if self.listener: self.listener.stop()


class DesktopBackend:
    def __init__(self):
        from pynput import keyboard, mouse
        self.keyboard_module = keyboard; self.keyboard = keyboard.Controller()
        self.mouse = mouse.Controller(); self.listener = None
    def allowed(self): return True
    def require_permission(self): pass
    def write(self, text): self.keyboard.type(text)
    def newline(self):
        with self.keyboard.pressed(self.keyboard_module.Key.shift):
            self.keyboard.press(self.keyboard_module.Key.enter); self.keyboard.release(self.keyboard_module.Key.enter)
    def listen_escape(self, callback):
        self.listener = self.keyboard_module.Listener(on_press=lambda key: callback() if key == self.keyboard_module.Key.esc else None); self.listener.start()
        wait_for_listener(self.listener)
    def escape_healthy(self): return bool(self.listener and self.listener.is_alive() and self.listener.running)
    def idle_seconds(self): raise RuntimeError('Mouse Jiggler bu sürümde macOS gerektirir.')
    def close(self):
        if self.listener: self.listener.stop()


def create_backend(): return MacBackend() if sys.platform == 'darwin' else DesktopBackend()

def open_permissions():
    if sys.platform == 'darwin': subprocess.Popen(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])

def play_sound(name):
    path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'sounds' / f'{name}.wav'
    if not path.exists(): return
    if sys.platform == 'darwin': subprocess.Popen(['/usr/bin/afplay', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == 'win32':
        import winsound
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
