#!/usr/bin/python3
"""Firefox native messaging bridge; stdout is reserved for framed JSON."""
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


def read_exact(size):
    data = bytearray()
    while len(data) < size:
        chunk = sys.stdin.buffer.read(size - len(data))
        if not chunk:
            raise ValueError('Incomplete message from Firefox.')
        data.extend(chunk)
    return bytes(data)


def download(message):
    url = message.get('url') if isinstance(message, dict) else None
    if not isinstance(url, str) or not url or len(url) > 16000:
        raise ValueError('Choose a video page or an HTTP(S) video link.')
    if any(ord(char) < 33 or ord(char) == 127 for char in url):
        raise ValueError('The video URL contains invalid characters.')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Only HTTP and HTTPS video URLs are supported.')
    if parsed.username is not None or parsed.password is not None:
        raise ValueError('URLs containing login credentials are not supported.')
    x_host = parsed.hostname.lower().removeprefix('www.').removeprefix('mobile.')
    if x_host in ('x.com', 'twitter.com') and (
        parsed.path.rstrip('/') in ('', '/home', '/login', '/i/timeline', '/i/flow/login')
        or parsed.path.startswith('/i/jf/onboarding/')
    ):
        raise ValueError('This is an X login or feed page. Open the individual post by clicking its timestamp, '
                         'then right-click and choose Download + transcribe to Desktop. '
                         'You can also right-click the post timestamp link directly.')
    transcribe = message.get('transcribe', False)
    if not isinstance(transcribe, bool):
        raise ValueError('The transcription option must be true or false.')
    engine = Path.home() / '.local/share/video-downloader-firefox'
    python = engine / 'venv/bin/python'
    worker = engine / 'transcribe.py'
    if transcribe and (not python.is_file() or not worker.is_file()):
        raise ValueError('Transcription is not installed. Run python3 install.py --transcription.')
    # Browser launches may have a smaller PATH than the interactive terminal.
    env = dict(os.environ)
    env['PATH'] = str(Path.home() / '.local/bin') + os.pathsep + env.get('PATH', '/usr/bin:/bin')
    downloader = shutil.which('yt-dlp', path=env['PATH'])
    if not downloader:
        raise ValueError('yt-dlp is missing. Install it and run install.py again.')
    if not shutil.which('ffmpeg', path=env['PATH']):
        raise ValueError('FFmpeg is missing. Install it to merge video and audio.')
    desktop = Path.home() / 'Desktop'
    xdg = shutil.which('xdg-user-dir', path=env['PATH'])
    if xdg:
        directory = subprocess.run([xdg, 'DESKTOP'], capture_output=True,
                                   text=True, env=env, timeout=10)
        if directory.returncode == 0 and directory.stdout.strip():
            candidate = Path(directory.stdout.strip())
            if candidate.is_absolute():
                desktop = candidate
    desktop.mkdir(parents=True, exist_ok=True)
    command = [downloader, '--ignore-config', '--no-plugin-dirs', '--no-playlist', '--playlist-items', '1',
               '--no-overwrites', '--restrict-filenames', '--no-progress',
               '-S', 'ext:mp4:m4a', '--merge-output-format', 'mp4',
               '--remux-video', 'mp4', '-P', str(desktop),
               '-o', '%(title).120B-%(id)s.%(ext)s',
               '--print', 'after_move:filepath', '--', url]
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        result = subprocess.run(command, stdout=output, stderr=errors,
                                env=env, timeout=21600, umask=0o077)
        if result.returncode:
            errors.seek(0, 2)
            errors.seek(max(0, errors.tell() - 3000))
            detail = errors.read().decode('utf-8', errors='replace').strip()
            raise ValueError(detail or 'This video could not be downloaded.')
        output.seek(0, 2)
        output.seek(max(0, output.tell() - 16000))
        paths = output.read().decode('utf-8', errors='replace').strip().splitlines()
        if not paths:
            raise ValueError('yt-dlp did not return a downloaded file.')
        path = Path(paths[-1]).resolve()
        if not path.is_file() or path.parent != desktop.resolve():
            raise ValueError('The downloaded file could not be verified on the Desktop.')
        response = {'ok': True, 'path': str(path)}
    if transcribe:
        with tempfile.TemporaryFile() as errors:
            result = subprocess.run([str(python), str(worker), str(path)],
                                    stdout=subprocess.PIPE, stderr=errors,
                                    env=env, timeout=21600)
            if result.returncode:
                errors.seek(0, 2)
                errors.seek(max(0, errors.tell() - 2000))
                detail = errors.read().decode('utf-8', errors='replace').strip()
                raise ValueError('Video saved at ' + str(path) +
                                 ', but transcription failed: ' + detail)
            outputs = json.loads(result.stdout)
            for key in ('transcript', 'subtitles'):
                saved = Path(outputs[key]).resolve()
                if not saved.is_file() or saved.parent != desktop.resolve():
                    raise ValueError('The transcript file could not be verified on the Desktop.')
                response[key] = str(saved)
    return response


def main():
    try:
        size = struct.unpack('=I', read_exact(4))[0]
        if not 0 < size <= 65536:
            raise ValueError('Firefox sent an oversized or empty message.')
        response = download(json.loads(read_exact(size)))
    except subprocess.TimeoutExpired:
        response = {'ok': False, 'error': 'The download or transcription timed out. Any saved video remains on Desktop.'}
    except (ValueError, OSError) as error:
        response = {'ok': False, 'error': str(error)}
    payload = json.dumps(response).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('=I', len(payload)) + payload)
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
