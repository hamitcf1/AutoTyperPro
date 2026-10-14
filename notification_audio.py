"""Per-app audio gain, without changing the system or other apps' volume."""
import array
import hashlib
import io
import sys
import wave
from pathlib import Path
THEMES=('classic','soft','glass')
EVENTS=('start','finish','stop','emergency')

def attenuate(content,volume):
    if type(volume) is not int or not 0<=volume<=100:raise ValueError('Invalid sound volume')
    with wave.open(io.BytesIO(content),'rb') as audio:
        params=audio.getparams()
        if params.sampwidth!=2 or params.comptype!='NONE':raise ValueError('Expected 16-bit PCM sound')
        samples=array.array('h',audio.readframes(params.nframes))
    if sys.byteorder!='little':samples.byteswap()
    samples=array.array('h',(round(sample*volume/100) for sample in samples))
    if sys.byteorder!='little':samples.byteswap()
    target=io.BytesIO()
    with wave.open(target,'wb') as audio:audio.setparams(params);audio.writeframes(samples.tobytes())
    return target.getvalue()

def sound_path(event,theme,volume,sound_dir,cache_dir):
    if event not in EVENTS or theme not in THEMES:raise ValueError('Unknown notification sound')
    if type(volume) is not int or not 0<=volume<=100:raise ValueError('Invalid sound volume')
    if volume==0:return None
    source=Path(sound_dir)/(event+'.wav' if theme=='classic' else theme+'-'+event+'.wav')
    if not source.is_file():return None
    if volume==100:return source
    content=source.read_bytes();digest=hashlib.sha256(content+str(volume).encode()).hexdigest()
    cache=Path(cache_dir);cache.mkdir(parents=True,exist_ok=True)
    path=cache/(digest+'.wav')
    if not path.exists():
        import os,tempfile
        handle,temp=tempfile.mkstemp(dir=cache,suffix='.wav')
        try:
            with os.fdopen(handle,'wb') as out:out.write(attenuate(content,volume))
            os.replace(temp,path)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    return path
