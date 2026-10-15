"""Validate catalogs and report missing keys without requiring a GUI."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from localization import translation_report
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path);args=parser.parse_args()
report=translation_report(args.root)
for value in report['locales'].values():value.pop('catalog')
print(json.dumps(report,ensure_ascii=True,indent=2))
raise SystemExit(bool(report['errors']))
