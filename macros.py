"""Validated local macro documents and cancellation-safe playback."""
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import time
import uuid
from localization import tr
from preferences import atomic_json, config_directory

MAX_EVENTS=10000
MAX_DURATION=300
BUTTONS=('left','right','middle','x1','x2')

@dataclass(frozen=True)
class MacroEvent:
    time: float
    kind: str
    data: dict

@dataclass(frozen=True)
class Macro:
    platform: str
    displays: list
    events: list
    def document(self): return asdict(self)


def number(value,low,high):
    if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError(tr('macro.invalid'))
    return value


def validate_layout(displays):
    if not isinstance(displays,list) or not 1<=len(displays)<=16:raise ValueError(tr('macro.invalid'))
    result=[]
    for display in displays:
        if not isinstance(display,dict) or set(display)!= {'left','top','width','height'}:raise ValueError(tr('macro.invalid'))
        result.append({key:number(value,1 if key in ('width','height') else -100000,100000) for key,value in display.items()})
    return result


def validate_macro(data):
    if isinstance(data,Macro):data=data.document()
    if not isinstance(data,dict) or data.get('platform') not in ('darwin','win32'):
        raise ValueError(tr('macro.invalid'))
    displays=validate_layout(data.get('displays'))
    events=data.get('events')
    if not isinstance(events,list) or not 1<=len(events)<=MAX_EVENTS:raise ValueError(tr('macro.invalid'))
    held=set();result=[];previous=0
    for event in events:
        if not isinstance(event,dict):raise ValueError(tr('macro.invalid'))
        when=number(event.get('time'),previous,MAX_DURATION);previous=when
        kind=event.get('kind');values=event.get('data')
        fields={'move':{'x','y'},'button':{'x','y','button','down'},'key':{'code','down'},'scroll':{'dx','dy'}}
        if kind not in fields or not isinstance(values,dict) or set(values)!=fields[kind]:raise ValueError(tr('macro.invalid'))
        if kind in ('move','button'):
            x=number(values['x'],-100000,100000);y=number(values['y'],-100000,100000)
            if not any(d['left']<=x<d['left']+d['width'] and d['top']<=y<d['top']+d['height'] for d in displays):raise ValueError(tr('macro.invalid'))
        if kind=='scroll':
            number(values['dx'],-1000,1000);number(values['dy'],-1000,1000)
        if kind in ('key','button'):
            if type(values['down']) is not bool:raise ValueError(tr('macro.invalid'))
            if kind=='key':
                code=values['code']
                if type(code) is not int or not 0<=code<=(127 if data['platform']=='darwin' else 255) or code==(53 if data['platform']=='darwin' else 27):raise ValueError(tr('macro.invalid'))
            else:
                code=values['button']
                if code not in BUTTONS:raise ValueError(tr('macro.invalid'))
            identity=(kind,code)
            if values['down']:
                if identity in held:raise ValueError(tr('macro.invalid'))
                held.add(identity)
            else:
                if identity not in held:raise ValueError(tr('macro.invalid'))
                held.remove(identity)
        result.append(MacroEvent(when,kind,dict(values)))
    if held:raise ValueError(tr('macro.invalid'))
    return Macro(data['platform'],displays,result)


def same_layout(a,b):return sorted(tuple(d[k] for k in ('left','top','width','height')) for d in a)==sorted(tuple(d[k] for k in ('left','top','width','height')) for d in b)


def fit_point(point,source,target):
    left=min(d['left'] for d in source);top=min(d['top'] for d in source)
    right=max(d['left']+d['width'] for d in source);bottom=max(d['top']+d['height'] for d in source)
    x,y=point
    return (min(target['left']+target['width']-1,target['left']+(x-left)*target['width']/(right-left)),min(target['top']+target['height']-1,target['top']+(y-top)*target['height']/(bottom-top)))


def play_macro(macro,backend,stop,events,speed=1.0,repeats=1,repeat_delay=0.0,start_delay=3.0,fit_to_primary=False):
    try:
        macro=validate_macro(macro)
        number(speed,.25,4);number(repeat_delay,0,3600);number(start_delay,0,60)
        if type(repeats) is not int or not 1<=repeats<=100:raise ValueError(tr('macro.invalid'))
        layout=validate_layout(backend.display_layout())
        if any(event.kind=='key' for event in macro.events) and macro.platform!=backend.native_platform:
            raise ValueError(tr('macro.platform_mismatch'))
        mismatch=not same_layout(layout,macro.displays)
        if mismatch and not fit_to_primary:raise ValueError(tr('macro.display_mismatch'))
        deadline=time.monotonic()+start_delay
        while not stop.is_set() and time.monotonic()<deadline:
            events.put(('macro_countdown',deadline-time.monotonic()));stop.wait(min(.1,max(0,deadline-time.monotonic())))
        if stop.is_set():events.put(('macro_stopped',None));return
        events.put(('macro_started',None))
        total=len(macro.events)*repeats;done=0
        for repeat in range(repeats):
            origin=time.monotonic()
            for event in macro.events:
                if stop.wait(max(0,origin+event.time/speed-time.monotonic())):break
                values=event.data
                point=(values['x'],values['y']) if event.kind in ('move','button') else None
                if mismatch and point:point=fit_point(point,macro.displays,layout[0])
                if event.kind=='move':backend.move_to(point)
                elif event.kind=='key':backend.physical_key_event(values['code'],values['down'])
                elif event.kind=='button':backend.button_event(values['button'],values['down'],point)
                elif event.kind=='scroll':backend.scroll_event(values['dx'],values['dy'])
                done+=1;events.put(('macro_progress',(done,total)))
            if stop.is_set():break
            if repeat+1<repeats and stop.wait(repeat_delay):break
        events.put(('macro_stopped' if stop.is_set() else 'macro_finished',None))
    except Exception as exc:events.put(('macro_error',str(exc)))
    finally:
        try:backend.release_held_inputs()
        except Exception as exc:events.put(('macro_error',str(exc)))


def valid_identity(value):
    if not isinstance(value,str):raise ValueError(tr('macro.invalid'))
    try:return str(uuid.UUID(value))
    except (ValueError,AttributeError) as exc:raise ValueError(tr('macro.invalid')) from exc


class MacroStore:
    def __init__(self,directory=None):self.directory=Path(directory) if directory else config_directory()/'macros'
    def save(self,name,macro,identity=None):
        macro=validate_macro(macro)
        if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ValueError(tr('macro.invalid_name'))
        identity=str(uuid.uuid4()) if identity is None else valid_identity(identity)
        atomic_json(self.directory/(identity+'.json'),{'schema':1,'id':identity,'name':name.strip(),'macro':macro.document()})
        return identity
    def list(self):
        result=[];self.errors=[]
        for path in sorted(self.directory.glob('*.json')):
            try:result.append(self.read_file(path))
            except ValueError:self.errors.append(path.name)
        return result
    @staticmethod
    def read_file(path):
        path=Path(path)
        try:
            if path.stat().st_size>4*1024*1024:raise ValueError(tr('macro.invalid'))
            data=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or data.get('schema')!=1:raise ValueError(tr('macro.invalid'))
            identity=valid_identity(data['id']);name=data['name']
            if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ValueError(tr('macro.invalid_name'))
            return {'id':identity,'name':name.strip(),'macro':validate_macro(data['macro'])}
        except (OSError,ValueError,TypeError,KeyError,RecursionError) as exc:raise ValueError(tr('macro.invalid')) from exc
    def import_file(self,path):
        data=self.read_file(path);self.save(data['name'],data['macro'],data['id']);return data
    def export_file(self,identity,path):
        identity=valid_identity(identity);data=self.read_file(self.directory/(identity+'.json'))
        atomic_json(path,{'schema':1,'id':identity,'name':data['name'],'macro':data['macro'].document()})
    def delete(self,identity):
        identity=valid_identity(identity);(self.directory/(identity+'.json')).unlink(missing_ok=True)
