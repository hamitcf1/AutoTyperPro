"""Build a branded DMG without GUI automation or Finder scripts."""
import os
import sys
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import tempfile
import time
from ds_store import DSStore
from mac_alias import Alias
from PIL import Image

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from preferences import VERSION
app=root/'dist/AutoTyperPro.app'
if not app.is_dir():raise SystemExit('Build AutoTyperPro.app first.')
output=root/'dist/installers';output.mkdir(exist_ok=True)
arch='arm64' if platform.machine()=='arm64' else 'x64'
target=output/f'AutoTyperPro-{VERSION}-macos-{arch}.dmg'
mount=None
with tempfile.TemporaryDirectory(prefix='autotyper-dmg-') as temp:
    temp=Path(temp);writable=temp/'install.dmg'
    def run(*args):return subprocess.check_output(args)
    def detach_owned_image(point):
        # Finder/Spotlight can briefly retain handles after icon generation.
        # Only this script's freshly created temporary volume is eligible.
        run('sync')
        for attempt in range(6):
            result=subprocess.run(['hdiutil','detach',str(point)],capture_output=True,text=True)
            if result.returncode==0:return
            if result.returncode!=16 and 'Resource busy' not in result.stderr:
                raise RuntimeError(result.stderr.strip())
            time.sleep(.5+attempt*.2)
        run('hdiutil','detach','-force',str(point))
    staging=temp/'source';staging.mkdir()
    (staging/'.metadata_never_index').touch()
    run('ditto',str(app),str(staging/app.name))
    run('hdiutil','create','-srcfolder',str(staging),'-size','256m','-fs','HFS+','-volname','AutoTyper Pro','-format','UDRW','-o',str(writable))
    attached=plistlib.loads(run('hdiutil','attach','-nobrowse','-plist',str(writable)))
    mount=next(Path(e['mount-point']) for e in attached['system-entities'] if 'mount-point' in e)
    try:
        (mount/'Applications').symlink_to('/Applications')
        background=mount/'.background';background.mkdir()
        (mount/'.metadata_never_index').touch()
        retina=Image.open(root/'assets/dmg-background.png')
        retina.resize((640,420),Image.Resampling.LANCZOS).save(background/'background.png',dpi=(72,72))
        retina.save(background/'background@2x.png',dpi=(144,144))
        run('tiffutil','-cathidpicheck',str(background/'background.png'),str(background/'background@2x.png'),'-out',str(background/'background.tiff'))
        shutil.copy2(root/'assets/icon.icns',mount/'.VolumeIcon.icns')
        info=bytearray(32);info[8]=4
        run('xattr','-wx','com.apple.FinderInfo',bytes(info).hex(),str(mount))
        with DSStore.open(str(mount/'.DS_Store'),'w+') as ds:
            ds['.']['vSrn']=('long',1)
            ds['.']['bwsp']={'WindowBounds':'{{200, 150}, {640, 420}}','ShowToolbar':False,'ShowSidebar':False,'ContainerShowSidebar':False,'PreviewPaneVisibility':False,'SidebarWidth':0,'ShowStatusBar':False,'ShowPathbar':False,'ShowTabView':False}
            ds['.']['icvp']={'viewOptionsVersion':1,'backgroundType':2,'backgroundImageAlias':Alias.for_file(str(background/'background.tiff')).to_bytes(),'backgroundColorRed':.08,'backgroundColorGreen':.09,'backgroundColorBlue':.08,'iconSize':104.0,'textSize':13.0,'labelOnBottom':True,'gridSpacing':100.0,'gridOffsetX':0.0,'gridOffsetY':0.0,'arrangeBy':'none','showIconPreview':True,'showItemInfo':False,'scrollPositionX':0.0,'scrollPositionY':0.0}
            ds['.']['icvl']=('type','icnv')
            ds[app.name]['Iloc']=(175,170)
            ds['Applications']['Iloc']=(465,170)
    finally:detach_owned_image(mount);mount=None
    run('hdiutil','convert',str(writable),'-format','UDZO','-imagekey','zlib-level=9','-ov','-o',str(target))
    run('hdiutil','verify',str(target))
print(target)
