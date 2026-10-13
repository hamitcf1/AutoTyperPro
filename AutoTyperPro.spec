# Shared, reproducible PyInstaller configuration.
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
mac = sys.platform == 'darwin'
icon = str(root / 'assets' / ('icon.icns' if mac else 'icon.ico'))
a = Analysis(
    [str(root / 'auto_typer.py')],
    pathex=[str(root)],
    datas=[(str(root / 'sounds'), 'sounds'),(str(root / 'assets/icon.png'),'assets'),(str(root / 'assets/icon.ico'),'assets')] + collect_data_files('customtkinter'),
    hiddenimports=['pynput.keyboard._darwin', 'pynput.mouse._darwin'] if mac else [],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='AutoTyperPro',
          debug=False, strip=False, upx=False, console=False, icon=icon,
          version=str(root/'packaging/windows/version.txt') if sys.platform=='win32' else None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='AutoTyperPro')
if mac:
    app = BUNDLE(coll, name='AutoTyperPro.app', icon=icon,
                 bundle_identifier='com.hamitcf.autotyperpro', version='2.1.0',
                 info_plist={'NSHighResolutionCapable': True,
                             'NSHumanReadableCopyright': 'AutoTyper Pro'})
