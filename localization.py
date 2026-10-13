"""English-first catalogs. Only idle UI actions change the current locale."""
import json
from pathlib import Path
import sys

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'locales'

class Translator:
    def __init__(self, locale='en'):
        self.locale = locale if locale in ('en','tr') else 'en'
        self.english = json.loads((ROOT/'en.json').read_text(encoding='utf-8'))
        self.catalog = self.english if self.locale == 'en' else json.loads((ROOT/'tr.json').read_text(encoding='utf-8'))
    def text(self,key,**values): return self.catalog.get(key,self.english.get(key,key)).format(**values)

_current = Translator()
def set_locale(locale):
    global _current
    _current = Translator(locale)
def tr(key,**values): return _current.text(key,**values)
