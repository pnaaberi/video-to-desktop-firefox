"""Manual live integration check: isolated headless Firefox and a real download."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import sys
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('url', help='Video URL to explicitly download for this live test')
parser.add_argument('--transcribe', action='store_true')
args = parser.parse_args()
received = []


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


with tempfile.TemporaryDirectory(prefix='video-extension-smoke-') as temp:
    extension = Path(temp) / 'extension'
    shutil.copytree(root / 'extension', extension)
    with HTTPServer(('127.0.0.1', 0), Receiver) as server:
        server.timeout = 55
        port = server.server_port
        manifest_path = extension / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['permissions'].append('http://127.0.0.1/*')
        manifest_path.write_text(json.dumps(manifest))
        with (extension / 'background.js').open('a') as script:
            script.write('''
download(VIDEO_URL, TRANSCRIBE).then(async () => {
  await fetch('http://127.0.0.1:PORT/result', {method: 'POST', body: JSON.stringify({
    badge: await browser.browserAction.getBadgeText({}),
    title: await browser.browserAction.getTitle({})
  })});
});
'''.replace('PORT', str(port)).replace('TRANSCRIBE', 'true' if args.transcribe else 'false')
   .replace('VIDEO_URL', json.dumps(args.url)))
        with (Path(temp) / 'browser.log').open('w+') as log:
            process = subprocess.Popen([
                'npx', '--yes', 'web-ext', 'run', '--no-config-discovery',
                '--source-dir', str(extension), '--firefox', '/usr/bin/firefox',
                '--no-reload', '--no-input', '--arg=-headless',
            ], stdout=log, stderr=log, start_new_session=True)
            try:
                server.handle_request()
                if not received:
                    log.seek(0)
                    raise AssertionError('Firefox did not return a result:\n' + log.read()[-3000:])
                assert received[0]['badge'] == 'OK', received[0]
                print('PASS: actual Firefox extension called the installed native helper.')
                print(received[0]['title'])
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGTERM)
                        process.wait(timeout=5)
