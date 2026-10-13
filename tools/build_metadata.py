"""Generate Windows metadata from the single application VERSION value."""
from pathlib import Path
import re

def write_windows_version(path,version):
    if not isinstance(version,str) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Expected a numeric major.minor.patch version')
    parts=tuple(map(int,version.split('.')))+(0,)
    if any(part>65535 for part in parts):raise ValueError('Version component exceeds Windows limits')
    text=f'''VSVersionInfo(
 ffi=FixedFileInfo(filevers={parts!r},prodvers={parts!r},mask=0x3f,flags=0,OS=0x40004,fileType=1,subtype=0,date=(0,0)),
 kids=[StringFileInfo([StringTable('040904B0',[
  StringStruct('CompanyName','hamitcf1'),StringStruct('FileDescription','AutoTyper Pro desktop tools'),
  StringStruct('FileVersion',{version!r}),StringStruct('InternalName','AutoTyperPro'),
  StringStruct('OriginalFilename','AutoTyperPro.exe'),StringStruct('ProductName','AutoTyper Pro'),
  StringStruct('ProductVersion',{version!r})])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])
'''
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    return str(path)
