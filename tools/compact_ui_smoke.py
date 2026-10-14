"""Real Tk layout checks, exclusively on the runner's invisible Windows desktop."""
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.windows_isolated_ui import WindowsDesktopAPI,validate_child
if sys.platform!='win32':raise SystemExit('Use windows_isolated_ui.py --test compact; no UI opened.')
validate_child(WindowsDesktopAPI(),os.environ.get('AUTOTYPER_TEST_DESKTOP'))
import customtkinter as ctk
from auto_typer import AutoTyper
from support_ui import report_bug

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)

def pump(root,seconds=.25):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:root.update();time.sleep(.01)

def inside(root,widget):
    left=widget.winfo_rootx()-root.winfo_rootx();top=widget.winfo_rooty()-root.winfo_rooty()
    bounds=(left,top,left+widget.winfo_width(),top+widget.winfo_height())
    assert widget.winfo_viewable() and bounds[0]>=-2 and bounds[1]>=-2 and bounds[2]<=root.winfo_width()+2 and bounds[3]<=root.winfo_height()+2,(widget,bounds,root.winfo_width(),root.winfo_height())

with tempfile.TemporaryDirectory(prefix='autotyper-layout-') as directory:
    os.environ['AUTOTYPER_CONFIG_DIR']=directory
    app=AutoTyper(show_intro=False);errors=[]
    app.root.report_callback_exception=lambda *args:errors.append(args)
    try:
        pump(app.root,1.2)
        for appearance in ('dark','light'):
            app.change_preferences(locale='en',appearance=appearance)
            for size in ('740x540','800x600','1120x800'):
                app.root.geometry(size);pump(app.root)
                for preferred in (.8,1.25):
                    app.preferences.update({'ui_scale':preferred});app.responsive_layout();pump(app.root)
                    inside(app.root,app.nav)
                    for page,buttons in [('Auto Typer',('start_btn','stop_btn')),('Mouse Jiggler',('jig_start_btn','jig_stop_btn')),('Macros',())]:
                        app.show_page(page);pump(app.root)
                        for name in buttons:inside(app.root,getattr(app,name))
                        if page=='Macros':inside(app.root,app.macro_page.play_button);inside(app.root,app.macro_page.record_button)
                    app.show_page('Settings');pump(app.root)
                    scroll=next(w for w in descendants(app.settings_page) if isinstance(w,ctk.CTkScrollableFrame))
                    scroll._parent_canvas.yview_moveto(1);pump(app.root)
                    save=next(w for w in descendants(app.settings_page) if isinstance(w,ctk.CTkButton) and w.cget('text')=='Save settings')
                    inside(app.root,save)
        report=report_bug(app);pump(app.root)
        preview=next(w for w in descendants(report) if isinstance(w,ctk.CTkTextbox))
        preview.insert('end','\nControlled report draft');draft=preview.get('1.0','end-1c')
        app.change_preferences(appearance='dark');pump(app.root)
        assert report.winfo_exists() and preview.get('1.0','end-1c')==draft
        report.destroy()
        app.preferences.update({'reduced_motion':False});app.show_introduction();app.intro.advance();pump(app.root,.3)
        assert float(app.intro.panel.place_info()['rely'])==.5
        app.intro.finish()
        assert not errors,errors
        print('Compact UI PASS: dark/light,740/800/1120 windows,80/125% preference, navigation/actions/settings viewport, report draft, intro motion')
    finally:app.close()
