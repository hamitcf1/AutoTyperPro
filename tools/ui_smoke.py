"""Exercise actual CTk controls with a fake backend; no input leaves the app."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import time
import tempfile
from unittest.mock import patch
from preferences import Preferences
from auto_typer import AutoTyper

class FakeBackend:
    def __init__(self): self.output=[];self.permitted=True
    def allowed(self): return self.permitted
    def listen_escape(self, callback): self.callback=callback
    def escape_healthy(self): return True
    def write(self,text): self.output.append(text)
    def newline(self): self.output.append('\n')
    def idle_seconds(self): return 0
    def micro_activity(self,f18,stop): return True
    def close(self): pass

app=AutoTyper(show_intro=False); app.backend.close(); app.backend=FakeBackend()
errors=[]
app.root.report_callback_exception=lambda *args: errors.append(args)
def pump(seconds=.3):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        app.root.update(); time.sleep(.01)
def pump_until(predicate,timeout=8):
    deadline=time.monotonic()+timeout
    while not predicate() and time.monotonic()<deadline:
        app.root.update();time.sleep(.01)
    assert predicate(),'UI activity did not settle before timeout'

app.root.geometry('980x740'); pump()
app.nav.set('Mouse Jiggler'); app.show_page('Mouse Jiggler'); pump()
assert app.jig_start_btn.winfo_viewable()
app.start_jiggler(); pump(); assert app.jiggler_thread.is_alive()
app.nav.set('Auto Typer'); app.show_page('Auto Typer'); pump()
app.start_typing(); assert not app.typing_active.is_set()
app.text_input.insert('1.0','İstanbul şğüöç'); pump()
app.start_delay.delete(0,'end'); app.start_delay.insert(0,'0')
app.speed.set('Çok hızlı'); app.settings_changed()
app.start_typing(); pump_until(lambda:not app.typing_active.is_set())
assert ''.join(app.backend.output)=='İstanbul şğüöç',app.backend.output
assert not app.typing_active.is_set()
assert app.progress.get()==1
app.start_delay.delete(0,'end'); app.start_delay.insert(0,'nan')
app.start_typing(); assert not app.typing_active.is_set()
app.start_delay.delete(0,'end'); app.start_delay.insert(0,'60')
app.start_typing(); pump(.2); app.emergency_stop()
pump_until(lambda:not app.typing_active.is_set() and not app.jiggler_thread.is_alive())
assert not app.typing_active.is_set()
assert not app.jiggler_thread.is_alive()
app.speed.set('Rastgele'); app.settings_changed(); pump()
assert app.random_frame.winfo_viewable()
app.backend.permitted=False;app.check_permissions();pump()
assert app.permission_bar.winfo_viewable()
app.backend.permitted=True;app.check_permissions();pump()
assert not app.permission_bar.winfo_viewable()
with tempfile.TemporaryDirectory() as d:
    app.preferences=Preferences(Path(d)/'intro.json')
    app.show_introduction();pump()
    assert app.intro is not None
    app.intro.advance();app.intro.advance();app.intro.advance();pump()
    assert app.intro is None and app.preferences.intro_complete()
    app.show_introduction();pump();app.intro.finish();pump()
    original_close=app.close;app.close=lambda:None
    app.restart();resume=app.restart_command[app.restart_command.index('--resume-state')+1]
    app.close=original_close
    original_text=app.text_input.get('1.0','end-1c');original_speed=app.speed.get()
    app.text_input.delete('1.0','end')
    app.restore_state(resume,app.restart_command[app.restart_command.index('--resume-token')+1])
    assert app.text_input.get('1.0','end-1c')==original_text
    assert app.speed.get()==original_speed
    assert not Path(resume).exists()
    app.restart_command=None
app.restart_command=['missing-program'];app.closing=True
with patch('auto_typer.subprocess.Popen',side_effect=OSError('test launch failure')):
    app.await_shutdown()
assert app.root.winfo_exists() and not app.closing
assert not errors,errors
app.close(); print('UI smoke PASS: minimum size, typing, jiggler, ESC, live permissions, intro persistence/replay, state-preserving restart, shutdown')
