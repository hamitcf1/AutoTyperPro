"""Reviewed local catalogs; partial translations fall back without executing code."""
import json
from pathlib import Path
import re
from string import Formatter
import sys

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'locales'
CODE=re.compile(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*\Z')

def _pairs(items):
    result={}
    for key,value in items:
        if key in result: raise ValueError(f'Duplicate key: {key}')
        result[key]=value
    return result

def _json(path):
    if path.stat().st_size>1024*1024: raise ValueError('Catalog exceeds 1 MiB')
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=_pairs)

def _fields(text):
    return {name for _,name,_,_ in Formatter().parse(text) if name is not None}

def _catalog(root,code,errors):
    try:
        value=_json(root/f'{code}.json')
        if not isinstance(value,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in value.items()): raise ValueError('Catalog must contain string keys and values')
        return value
    except (OSError,ValueError,RecursionError) as error:
        errors.append(f'{code}: {error}');return {}

def translation_report(root=None):
    root=Path(root or ROOT);errors=[];base=_catalog(root,'en',errors)
    entries=[{'code':'en','native_name':'English','contributors':[]}]
    try:
        manifest=_json(root/'manifest.json')
        if not isinstance(manifest,dict) or manifest.get('default')!='en' or not isinstance(manifest.get('locales'),list): raise ValueError('Manifest requires default en and a locales array')
        checked=[];seen=set()
        for entry in manifest['locales']:
            if not isinstance(entry,dict):raise ValueError('Invalid locale metadata')
            code=entry.get('code');label=entry.get('native_name');credits=entry.get('contributors',[])
            if not isinstance(code,str) or not CODE.fullmatch(code) or code in seen:raise ValueError('Invalid or duplicate locale code')
            if not isinstance(label,str) or not label.strip() or len(label)>80 or not isinstance(credits,list) or any(not isinstance(c,str) or len(c)>100 for c in credits):raise ValueError('Invalid locale label or contributors')
            seen.add(code);checked.append({'code':code,'native_name':label,'contributors':credits})
        if 'en' not in seen:raise ValueError('Manifest must include en')
        entries=checked
    except (OSError,ValueError,RecursionError) as error:errors.append(f'manifest: {error}')
    locales={}
    for entry in entries:
        code=entry['code'];catalog=base if code=='en' else _catalog(root,code,errors);valid={}
        for key,text in catalog.items():
            if key not in base:
                errors.append(f'{code}: unknown key {key}');continue
            try:
                if _fields(text)!=_fields(base[key]):raise ValueError('placeholder mismatch')
                valid[key]=text
            except ValueError as error: errors.append(f'{code}: {key}: {error}')
        locales[code]={**entry,'translated':len(valid),'total':len(base),'missing':sorted(set(base)-set(valid)),'catalog':valid}
    return {'default':'en','locales':locales,'errors':errors}

def locale_options(root=None):
    return [(code,data['native_name']) for code,data in translation_report(root)['locales'].items()]

class Translator:
    def __init__(self,locale='en',root=None):
        report=translation_report(root)
        self.locale=locale if locale in report['locales'] else 'en'
        self.english=report['locales'].get('en',{}).get('catalog',{})
        self.catalog=report['locales'][self.locale]['catalog']
    def text(self,message_id,**values):return self.catalog.get(message_id,self.english.get(message_id,message_id)).format(**values)

_current=Translator()
def set_locale(locale):
    global _current
    _current=Translator(locale)
def tr(message_id,**values):return _current.text(message_id,**values)
