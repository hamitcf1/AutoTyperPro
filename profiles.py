"""Versioned local profiles. Imports are validated before any store mutation."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import uuid
from engine import TypingConfig, JigglerConfig
from preferences import atomic_json, config_directory


def new_profile(name, kind, config):
    return {'id':str(uuid.uuid4()), 'name':name, 'kind':kind, 'config':deepcopy(config)}


def validate_profile(data):
    if not isinstance(data,dict): raise ValueError('Invalid profile')
    try:
        uuid.UUID(data['id'])
        name = data['name']
        if not isinstance(name,str) or not 1 <= len(name.strip()) <= 80: raise ValueError('Invalid profile name')
        kind = data['kind']; config = data['config']
        if kind not in ('typing','activity') or not isinstance(config,dict): raise ValueError('Invalid profile type')
        config_type = TypingConfig if kind == 'typing' else JigglerConfig
        validated = config_type(**config).validate()
        return {'id':data['id'],'name':name.strip(),'kind':kind,'config':asdict(validated)}
    except (KeyError,TypeError,AttributeError,OverflowError) as exc:
        raise ValueError('Invalid profile') from exc


class ProfileStore:
    def __init__(self,path=None): self.path = Path(path) if path else config_directory() / 'profiles.json'
    def load(self):
        if not self.path.exists(): return []
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or data.get('schema') != 1 or not isinstance(data.get('profiles'),list): raise ValueError('Invalid profile store')
            profiles = [validate_profile(item) for item in data['profiles']]
            if len({item['id'] for item in profiles}) != len(profiles): raise ValueError('Duplicate profile IDs')
            return profiles
        except (OSError,ValueError) as exc: raise ValueError('Cannot read profiles; existing data was preserved') from exc
    def save(self,profile):
        profile = validate_profile(profile)
        items = [item for item in self.load() if item['id'] != profile['id']]
        items.append(profile)
        atomic_json(self.path, {'schema':1,'profiles':items})
    def delete(self,identity):
        atomic_json(self.path, {'schema':1,'profiles':[item for item in self.load() if item['id'] != identity]})
    def import_file(self,path):
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            if not isinstance(data,dict) or data.get('schema') != 1: raise ValueError('Unsupported profile file')
            profile = validate_profile(data['profile'])
        except (OSError,ValueError,KeyError,TypeError) as exc: raise ValueError('Invalid profile file') from exc
        self.save(profile)
        return profile
    def export_file(self,profile,path): atomic_json(path, {'schema':1,'profile':validate_profile(profile)})
