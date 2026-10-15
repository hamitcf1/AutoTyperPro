"""Check that the real entry point shares one theme with all tool pages."""
from pathlib import Path
import json
import os
import runpy
import sys
import tempfile
from unittest.mock import patch
import customtkinter as ctk
root_path=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root_path))
with tempfile.TemporaryDirectory() as directory:
    os.environ['AUTOTYPER_CONFIG_DIR']=directory
    Path(directory,'preferences.json').write_text(json.dumps({'schema':1,'appearance':'light','locale':'en','intro_complete':True}))
    def verify(root):
        module=sys.modules['__main__'];app=module.app
        try:
            root.update()
            assert app.macro_page.canvas.cget('bg')==module.INSET,'Macro page uses a different theme from the main window'
            assert app.desktop.ready,'Native desktop did not initialize'
            app.show_introduction()
            assert app.intro.panel.cget('fg_color')==module.PANEL,'Introduction must match the light theme'
            app.intro.finish()
            print('Entry-point UI PASS: one theme across pages, native quick access initialized')
        finally:app.close()
    with patch.object(ctk.CTk,'mainloop',verify),patch.object(sys,'argv',['auto_typer.py','--skip-intro']):
        runpy.run_path(str(root_path/'auto_typer.py'),run_name='__main__')
