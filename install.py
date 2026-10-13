#!/usr/bin/python3
"""Install this user's Linux Firefox native helper, without root."""
import json
from pathlib import Path
import shutil
import argparse
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--transcription', action='store_true', help='Install local Whisper and download its multilingual base model')
args = parser.parse_args()

source = Path(__file__).resolve().parent
target = Path.home() / '.local/share/video-downloader-firefox'
target.mkdir(parents=True, exist_ok=True)
shutil.copy2(source / 'host.py', target / 'host.py')
(target / 'host.py').chmod(0o755)
shutil.copy2(source / 'transcribe.py', target / 'transcribe.py')
if args.transcription:
    python = target / 'venv/bin/python'
    if not python.is_file():
        interpreter = shutil.which('python3.11') or shutil.which('python3.12')
        if not interpreter:
            parser.error('Transcription setup requires Python 3.11 or 3.12. Install one and try again.')
        subprocess.run([interpreter, '-m', 'venv', str(target / 'venv')], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '--upgrade', 'pip>=26.2', 'setuptools>=83'], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(source / 'requirements-transcription.txt')], check=True)
    subprocess.run([str(python), '-c',
                    'from faster_whisper.utils import download_model; import sys; '
                    'download_model("base", output_dir=sys.argv[1])',
                    str(target / 'models/base')], check=True)
manifest = {
    'name': 'video_downloader',
    'description': 'Download a video to Desktop with yt-dlp',
    'path': str(target / 'host.py'),
    'type': 'stdio',
    'allowed_extensions': ['video-downloader@local.invalid'],
}
directory = Path.home() / '.mozilla/native-messaging-hosts'
directory.mkdir(parents=True, exist_ok=True)
path = directory / 'video_downloader.json'
path.write_text(json.dumps(manifest, indent=2) + '\n')
print('Installed native helper:', path)
