"""Test fixtures without OS hooks, input, audio or native desktop UI."""
class FakeBackend:
    def __init__(self):
        import threading
        self.output=[];self.permitted=True;self.lock=threading.RLock();self.native_platform='darwin'
    def allowed(self): return self.permitted
    def listen_escape(self, callback): self.callback=callback
    def escape_healthy(self): return True
    def write(self,text): self.output.append(text)
    def newline(self): self.output.append('\n')
    def idle_seconds(self): return 0
    def micro_activity(self,f18,stop): return True
    def display_layout(self):return [{'left':0,'top':0,'width':100,'height':100}]
    def move_to(self,point):self.output.append(point)
    def release_held_inputs(self):pass
    def listen_events(self,callback,capture):
        class Listener:
            def stop(self):pass
            def join(self,timeout=None):pass
        callback('move',{'x':2,'y':3});callback('move',{'x':4,'y':5})
        return Listener()
    def close(self): pass

class FakeDesktop:
    def __init__(self):self.ready=False
    def start(self):self.ready=True;return True
    def stop(self):self.ready=False
    def update(self,*args):pass
    def request_notifications(self,callback):callback(False)
    def notify(self,*args):return False
