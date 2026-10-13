"""Recommended profiles and display-bounded mouse activity."""
from dataclasses import asdict
from engine import JigglerConfig

PRESETS = {
    'gentle':JigglerConfig(),
    'balanced':JigglerConfig(interval=60,distance=4),
    'keyboard':JigglerConfig(interval=60,movement='off',key='f18'),
}

def migrate_activity(data):
    data = dict(data)
    if 'f18' in data:
        old = data.pop('f18')
        data.setdefault('key','f18' if old else None)
    return data

def xy(point): return (point.x,point.y) if hasattr(point,'x') else tuple(point)

def activity_path(origin,bounds,config):
    x,y=origin;left,top,right,bottom=bounds
    delta=config.distance
    nx=min(right-1,x+delta) if x+delta < right else max(left,x-delta)
    ny=min(bottom-1,y+delta) if y+delta < bottom else max(top,y-delta)
    if config.movement == 'horizontal_return': return [(nx,y)]
    if config.movement == 'vertical_return': return [(x,ny)]
    if config.movement == 'square': return [(nx,y),(nx,ny),(x,ny)]
    return []

def perform_activity(backend,config,stop):
    config.validate()
    if stop.is_set(): return False
    origin=xy(backend.position());current=origin
    path=activity_path(origin,backend.screen_bounds(origin),config)
    moved=False
    try:
        for target in path:
            if stop.is_set(): break
            if moved and any(abs(a-b)>.5 for a,b in zip(xy(backend.position()),current)):
                return True
            backend.move_to(target);current=target;moved=True
            stop.wait(config.duration_ms/1000/max(1,len(path)))
    finally:
        if moved and all(abs(a-b)<=.5 for a,b in zip(xy(backend.position()),current)):
            backend.move_to(origin)
    if config.key and not stop.is_set(): backend.key_chord(config.key,tuple(config.modifiers),stop)
    return moved or bool(config.key and not stop.is_set())
