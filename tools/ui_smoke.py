"""Exercise actual CTk controls with a fake backend; no input leaves the app."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import time
import os
import tempfile
from unittest.mock import patch
from preferences import Preferences
from auto_typer import AutoTyper

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

config_directory=tempfile.TemporaryDirectory()
os.environ['AUTOTYPER_CONFIG_DIR']=config_directory.name
Path(config_directory.name,'profiles.json').write_text('{broken')
macro_directory=Path(config_directory.name,'macros');macro_directory.mkdir()
(macro_directory/'invalid.json').write_text('{"schema":1,"id":[],"name":"broken"}')
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
with tempfile.TemporaryDirectory() as locale_dir:
    app.preferences=Preferences(Path(locale_dir)/'prefs.json')
    app.text_input.insert('1.0','Draft survives language changes')
    app.speed.set('slow');app.newline.set('shift_enter')
    for locale,appearance in [('tr','light'),('en','system'),('en','dark')]:
        app.change_preferences(locale=locale,appearance=appearance);pump()
        assert app.text_input.get('1.0','end-1c')=='Draft survives language changes'
        assert app.speed.get()=='slow' and app.newline.get()=='shift_enter'
    app.text_input.delete('1.0','end');app.speed.set('balanced');app.newline.set('space')

app.nav.set('Mouse Jiggler'); app.show_page('Mouse Jiggler'); pump()
assert app.jig_start_btn.winfo_viewable()
app.activity_page.select_preset('Balanced'); assert app.activity_page.config().distance==4
app.activity_page.apply({'distance':12,'movement':'vertical_return','key':'f18','modifiers':['control']})
assert app.activity_page.config().modifiers==('control',)
app.activity_page.select_preset('Gentle · Recommended')
app.start_jiggler(); pump(); assert app.jiggler_thread.is_alive()
app.nav.set('Auto Typer'); app.show_page('Auto Typer'); pump()
app.start_typing(); assert not app.typing_active.is_set()
app.text_input.insert('1.0','İstanbul şğüöç'); pump()
app.start_delay.delete(0,'end'); app.start_delay.insert(0,'0')
app.speed.set('very_fast'); app.settings_changed()
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
app.speed.set('random'); app.settings_changed(); pump()
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
app.show_page('Macros');pump()
app.macro_page.entries['start_delay'].delete(0,'end');app.macro_page.entries['start_delay'].insert(0,'0')
app.macro_page.start_record();pump(.5);assert app.macro_active.is_set()
app.start_typing();assert not app.typing_active.is_set()
app.emergency_stop();pump_until(lambda:not app.macro_active.is_set())
assert app.macro_page.draft and app.macro_page.draft.events[0].data=={'x':2,'y':3}
app.macro_page.start_play();pump_until(lambda:not app.macro_active.is_set())
assert app.backend.output[-1]==(2,3)
assert not errors,errors
app.close(); print('UI smoke PASS: minimum size, typing, jiggler, ESC, live permissions, intro persistence/replay, state-preserving restart, shutdown')
