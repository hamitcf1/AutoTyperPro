"""Check a release tag and optional built macOS bundle against source metadata."""
import argparse
import json
from pathlib import Path
import plistlib
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preferences import VERSION
from localization import translation_report

parser=argparse.ArgumentParser();parser.add_argument('--tag');parser.add_argument('--app',type=Path)
args=parser.parse_args()
if args.tag and args.tag!='v'+VERSION:raise SystemExit('Release tag does not match application version')
root=Path(__file__).resolve().parents[1]
report=translation_report()
if report['errors']:raise SystemExit('Invalid locale catalogs: '+ '; '.join(report['errors']))
catalogs={code:json.loads((root/'locales'/f'{code}.json').read_text()) for code in report['locales']}
if args.app:
    info=plistlib.loads((args.app/'Contents/Info.plist').read_bytes())
    if info.get('CFBundleShortVersionString')!=VERSION:raise SystemExit('Bundle version mismatch')
    manifest=json.loads((root/'locales/manifest.json').read_text())
    if json.loads((args.app/'Contents/Resources/locales/manifest.json').read_text())!=manifest:raise SystemExit('Bundled locale registry mismatch')
    for code in catalogs:
        actual=json.loads((args.app/'Contents/Resources/locales'/f'{code}.json').read_text())
        if actual!=catalogs[code]:raise SystemExit('Bundled locale mismatch: '+code)
print(json.dumps({'version':VERSION,'locales':list(catalogs),'bundle_verified':bool(args.app)}))
