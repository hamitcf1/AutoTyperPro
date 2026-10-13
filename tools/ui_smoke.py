"""Exercise actual CTk controls with a fake backend; no input leaves the app."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import time
from auto_typer import AutoTyper

class FakeBackend:
    def __init__(self): self.output=[]
    def allowed(self): return True
    def listen_escape(self, callback): self.callback=callback
    def escape_healthy(self): return True
    def write(self,text): self.output.append(text)
    def newline(self): self.output.append('\n')
    def idle_seconds(self): return 0
    def micro_activity(self,f18,stop): return True
    def close(self): pass

app=AutoTyper(); app.backend.close(); app.backend=FakeBackend()
errors=[]
app.root.report_callback_exception=lambda *args: errors.append(args)
def pump(seconds=.3):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        app.root.update(); time.sleep(.01)

app.root.geometry('980x740'); pump()
app.nav.set('Mouse Jiggler'); app.show_page('Mouse Jiggler'); pump()
assert app.jig_start_btn.winfo_viewable()
app.start_jiggler(); pump(); assert app.jiggler_thread.is_alive()
app.nav.set('Auto Typer'); app.show_page('Auto Typer'); pump()
app.start_typing(); assert not app.typing_active.is_set()
app.text_input.insert('1.0','İstanbul şğüöç'); pump()
app.start_delay.delete(0,'end'); app.start_delay.insert(0,'0')
app.speed.set('Çok hızlı'); app.settings_changed()
app.start_typing(); pump(1)
assert ''.join(app.backend.output)=='İstanbul şğüöç',app.backend.output
assert not app.typing_active.is_set()
assert app.progress.get()==1
app.start_delay.delete(0,'end'); app.start_delay.insert(0,'nan')
app.start_typing(); assert not app.typing_active.is_set()
app.start_delay.delete(0,'end'); app.start_delay.insert(0,'60')
app.start_typing(); pump(.2); app.emergency_stop(); pump(.3)
assert not app.typing_active.is_set()
assert not app.jiggler_thread.is_alive()
app.speed.set('Rastgele'); app.settings_changed(); pump()
assert app.random_frame.winfo_viewable()
assert not errors,errors
app.close(); print('UI smoke PASS: minimum size, navigation, typing, empty text, invalid settings, random mode, jiggler, ESC, shutdown')
