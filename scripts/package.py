"""Build unsigned Firefox extension packages with reproducible ZIP metadata."""
import json
from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
version = json.loads((root / 'extension/manifest.json').read_text())['version']
output = root / 'dist'
output.mkdir(exist_ok=True)
archive = output / f'video-to-desktop-{version}.xpi'
files = [(p.name, p) for p in sorted((root / 'extension').iterdir()) if p.is_file()]
files.extend((name, root / name) for name in ['LICENSE', 'THIRD_PARTY.md'])
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
    for name, path in files:
        info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        package.writestr(info, path.read_bytes())
shutil.copyfile(archive, archive.with_suffix('.zip'))
print('Built unsigned packages in dist/ for version', version)
