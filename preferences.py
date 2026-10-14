"""Small local preference store. Language, appearance and intro status; no text or telemetry."""
import json
import os
from pathlib import Path
import sys
import tempfile

VERSION = '3.0.0'


def resource(name):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / name


def config_directory():
    override = os.environ.get('AUTOTYPER_CONFIG_DIR')
    if override: return Path(override)
    if sys.platform == 'win32': return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'AutoTyperPro'
    return Path.home() / 'Library' / 'Application Support' / 'AutoTyperPro'


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
            temp = Path(file.name)
            json.dump(data, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.flush(); os.fsync(file.fileno())
        temp.replace(path)
    finally:
        if temp: temp.unlink(missing_ok=True)


class Preferences:
    DEFAULTS = {'schema':1, 'intro_complete':False, 'locale':'en', 'appearance':'dark', 'sound':True, 'notifications':False, 'keep_running':False, 'reduced_motion':True}

    def __init__(self, path=None):
        self.path = Path(path) if path else config_directory() / 'preferences.json'

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('schema', 1) != 1: return dict(self.DEFAULTS)
            result = dict(self.DEFAULTS)
            for key, value in data.items():
                if key in self.DEFAULTS:
                    try: self.validate({key:value}); result[key] = value
                    except ValueError: pass
            return result
        except (OSError, ValueError): return dict(self.DEFAULTS)

    @staticmethod
    def validate(values):
        for key, value in values.items():
            if key == 'locale':
                from localization import locale_options
                if isinstance(value,str) and value in dict(locale_options()): continue
            if key == 'appearance' and value in ('dark','light','system'): continue
            if key in ('intro_complete','sound','notifications','keep_running','reduced_motion') and isinstance(value,bool): continue
            if key == 'schema' and type(value) is int and value == 1: continue
            raise ValueError('Invalid preference: ' + str(key))

    def update(self, values):
        self.validate(values)
        data = self.load(); data.update(values)
        atomic_json(self.path, data)

    def intro_complete(self): return self.load()['intro_complete']
    def complete_intro(self): self.update({'intro_complete':True})
