"""Check a release tag and optional built macOS bundle against source metadata."""
import argparse
import json
from pathlib import Path
import plistlib
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preferences import VERSION

parser=argparse.ArgumentParser();parser.add_argument('--tag');parser.add_argument('--app',type=Path)
args=parser.parse_args()
if args.tag and args.tag!='v'+VERSION:raise SystemExit('Release tag does not match application version')
root=Path(__file__).resolve().parents[1]
catalogs={code:json.loads((root/'locales'/f'{code}.json').read_text()) for code in ('en','tr')}
if set(catalogs['en'])!=set(catalogs['tr']):raise SystemExit('Locale catalogs differ')
if args.app:
    info=plistlib.loads((args.app/'Contents/Info.plist').read_bytes())
    if info.get('CFBundleShortVersionString')!=VERSION:raise SystemExit('Bundle version mismatch')
    for code in catalogs:
        actual=json.loads((args.app/'Contents/Resources/locales'/f'{code}.json').read_text())
        if actual!=catalogs[code]:raise SystemExit('Bundled locale mismatch: '+code)
print(json.dumps({'version':VERSION,'locales':list(catalogs),'bundle_verified':bool(args.app)}))
