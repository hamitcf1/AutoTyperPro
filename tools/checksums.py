from pathlib import Path
import hashlib
import platform
root=Path(__file__).resolve().parents[1]/'dist/installers'
lines=[]
for p in sorted(root.iterdir()):
    if p.suffix.lower() not in ('.dmg','.exe','.zip'):continue
    lines.append(f'{hashlib.file_digest(p.open("rb"),"sha256").hexdigest()}  {p.name}')
if not lines:raise SystemExit('No installer assets found')
(root/f'SHA256SUMS-{platform.system().lower()}-{platform.machine().lower()}.txt').write_text('\n'.join(lines)+'\n')
