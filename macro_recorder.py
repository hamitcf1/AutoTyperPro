"""Explicit, bounded recording. No keyboard text or layout queries are used."""
import threading
import time
from macros import Macro, MacroEvent, MAX_EVENTS, MAX_DURATION, validate_macro
from localization import tr

class Recorder:
    def __init__(self,backend,capture,events):
        if not capture or not set(capture)<= {'move','button','key','scroll'}:raise ValueError(tr('macro.invalid'))
        self.backend=backend;self.capture=capture;self.events=events
        self.lock=threading.RLock();self.active=False;self.listener=None
        self.recorded=[];self.held={};self.last_move=None;self.started=None;self.displays=None
    def start(self):
        self.displays=self.backend.display_layout();self.started=time.monotonic();self.active=True
        try:self.listener=self.backend.listen_events(self.accept,self.capture)
        except Exception:self.active=False;raise
    def limit_reached(self):
        with self.lock:
            if self.active and time.monotonic()-self.started>=MAX_DURATION:
                self.active=False;self.events.put(('record_limit',None))
            return not self.active
    def accept(self,kind,data):
        with self.lock:
            if not self.active:return
            elapsed=max(0,time.monotonic()-self.started)
            if elapsed>=MAX_DURATION:
                self.active=False;self.events.put(('record_limit',None));return
            if kind=='key' and data['code']==(53 if self.backend.native_platform=='darwin' else 27):
                self.active=False;return
            if kind not in self.capture:return
            if kind=='move' and self.last_move is not None and elapsed-self.last_move<1/30:return
            identity=(kind,data.get('code') if kind=='key' else data.get('button'))
            held_count=len(self.held)
            if kind in ('key','button'):
                if data['down'] and identity in self.held:return
                if not data['down'] and identity not in self.held:return
                held_count+=1 if data['down'] else -1
            if len(self.recorded)+1+held_count>MAX_EVENTS:
                self.active=False;self.events.put(('record_limit',None));return
            if kind=='move':self.last_move=elapsed
            self.recorded.append(MacroEvent(elapsed,kind,dict(data)))
            if kind in ('key','button'):
                if data['down']:self.held[identity]=dict(data)
                else:self.held.pop(identity,None)
    def stop(self):
        with self.lock:self.active=False
        if self.listener:
            self.listener.stop();self.listener.join(timeout=2)
            if hasattr(self.listener,'is_alive') and self.listener.is_alive():raise RuntimeError(tr('macro.listener_stop'))
        with self.lock:
            elapsed=min(MAX_DURATION,max(0,time.monotonic()-self.started))
            for (kind,code),data in reversed(list(self.held.items())):
                released=dict(data);released['down']=False
                self.recorded.append(MacroEvent(elapsed,kind,released))
            self.held.clear()
            if not self.recorded:raise ValueError(tr('macro.no_events'))
            return validate_macro(Macro(self.backend.native_platform,self.displays,self.recorded))
