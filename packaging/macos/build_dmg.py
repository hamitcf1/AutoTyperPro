"""Build a branded DMG without GUI automation or Finder scripts."""
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import tempfile
from ds_store import DSStore
from mac_alias import Alias
from PIL import Image

root=Path(__file__).resolve().parents[2]
app=root/'dist/AutoTyperPro.app'
if not app.is_dir():raise SystemExit('Build AutoTyperPro.app first.')
output=root/'dist/installers';output.mkdir(exist_ok=True)
arch='arm64' if platform.machine()=='arm64' else 'x64'
target=output/f'AutoTyperPro-2.1.0-macos-{arch}.dmg'
mount=None
with tempfile.TemporaryDirectory(prefix='autotyper-dmg-') as temp:
    temp=Path(temp);writable=temp/'install.dmg'
    def run(*args):return subprocess.check_output(args)
    staging=temp/'source';staging.mkdir()
    run('ditto',str(app),str(staging/app.name))
    run('hdiutil','create','-srcfolder',str(staging),'-size','256m','-fs','HFS+','-volname','AutoTyper Pro','-format','UDRW','-o',str(writable))
    attached=plistlib.loads(run('hdiutil','attach','-nobrowse','-plist',str(writable)))
    mount=next(Path(e['mount-point']) for e in attached['system-entities'] if 'mount-point' in e)
    try:
        (mount/'Applications').symlink_to('/Applications')
        background=mount/'.background';background.mkdir()
        Image.open(root/'assets/dmg-background.png').resize((640,420),Image.Resampling.LANCZOS).save(background/'background.png')
        shutil.copy2(root/'assets/icon.icns',mount/'.VolumeIcon.icns')
        info=bytearray(32);info[8]=4
        run('xattr','-wx','com.apple.FinderInfo',bytes(info).hex(),str(mount))
        with DSStore.open(str(mount/'.DS_Store'),'w+') as ds:
            ds['.']['vSrn']=('long',1)
            ds['.']['bwsp']={'WindowBounds':'{{200, 150}, {640, 420}}','ShowToolbar':False,'ShowSidebar':False,'ContainerShowSidebar':False,'PreviewPaneVisibility':False,'SidebarWidth':0,'ShowStatusBar':False,'ShowPathbar':False,'ShowTabView':False}
            ds['.']['icvp']={'viewOptionsVersion':1,'backgroundType':2,'backgroundImageAlias':Alias.for_file(str(background/'background.png')).to_bytes(),'backgroundColorRed':.08,'backgroundColorGreen':.09,'backgroundColorBlue':.08,'iconSize':104.0,'textSize':13.0,'labelOnBottom':True,'gridSpacing':100.0,'gridOffsetX':0.0,'gridOffsetY':0.0,'arrangeBy':'none','showIconPreview':True,'showItemInfo':False,'scrollPositionX':0.0,'scrollPositionY':0.0}
            ds['.']['icvl']=('type','icnv')
            ds[app.name]['Iloc']=(175,170)
            ds['Applications']['Iloc']=(465,170)
    finally:run('hdiutil','detach',str(mount));mount=None
    run('hdiutil','convert',str(writable),'-format','UDZO','-imagekey','zlib-level=9','-ov','-o',str(target))
    run('hdiutil','verify',str(target))
print(target)
