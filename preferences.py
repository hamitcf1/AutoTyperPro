"""Small local preference store. Intro status only; no text or telemetry."""
import json
import os
from pathlib import Path
import sys
import tempfile

VERSION = '2.1.0'


def resource(name):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / name


def config_directory():
    override = os.environ.get('AUTOTYPER_CONFIG_DIR')
    if override: return Path(override)
    if sys.platform == 'win32': return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'AutoTyperPro'
    return Path.home() / 'Library' / 'Application Support' / 'AutoTyperPro'


class Preferences:
    def __init__(self, path=None): self.path = Path(path) if path else config_directory() / 'preferences.json'
    def intro_complete(self):
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            return isinstance(data,dict) and data.get('intro_complete') is True
        except (OSError,ValueError): return False
    def complete_intro(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.path.parent,delete=False) as f:
            json.dump({'intro_complete':True},f); temp=Path(f.name)
        try: temp.replace(self.path)
        finally: temp.unlink(missing_ok=True)
