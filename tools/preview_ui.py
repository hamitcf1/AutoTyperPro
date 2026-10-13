"""Open a real, idle UI page for manual visual review; no input is started."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from auto_typer import AutoTyper
from localization import tr
parser=argparse.ArgumentParser();parser.add_argument('--page',choices=['typing','activity','macros','settings'],default='typing');args=parser.parse_args()
app=AutoTyper(show_intro=False)
page={'typing':'Auto Typer','activity':tr('nav.activity'),'macros':tr('nav.macros'),'settings':tr('settings.title')}[args.page]
app.nav.set(page);app.show_page(page);app.run()
