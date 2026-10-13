import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import stat

HOST = Path(__file__).resolve().parents[1] / 'host.py'


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        binary = self.home / '.local/bin/yt-dlp'
        binary.parent.mkdir(parents=True)
        binary.write_text('''#!/usr/bin/python3
import sys
from pathlib import Path
args = sys.argv[1:]
assert '--ignore-config' in args and '--no-overwrites' in args
assert '--no-plugin-dirs' in args
assert '--no-playlist' in args and '--playlist-items' in args
assert args[-2] == '--'
if 'unsupported' in args[-1]:
    print('ERROR: Unsupported URL', file=sys.stderr)
    sys.exit(1)
target = Path(args[args.index('-P') + 1]) / 'test-video.mp4'
target.write_bytes(b'video fixture')
print(target)
''')
        binary.chmod(0o755)
        # The controlled downloader does not invoke FFmpeg, but the host checks
        # that it is installed. Keep that prerequisite independent of the OS.
        ffmpeg = binary.parent / 'ffmpeg'
        ffmpeg.write_text('#!/bin/sh\nexit 99\n')
        ffmpeg.chmod(0o755)
        xdg = self.home / '.local/bin/xdg-user-dir'
        xdg.write_text('#!/bin/sh\nprintf "%s/Desktop\\n" "$HOME"\n')
        xdg.chmod(0o755)

    def exchange(self, message=None, raw=None):
        if raw is None:
            payload = json.dumps(message).encode()
            raw = struct.pack('=I', len(payload)) + payload
        env = dict(os.environ, HOME=str(self.home),
                   PATH=str(self.home / '.local/bin') + ':/usr/bin:/bin')
        result = subprocess.run([sys.executable, str(HOST)], input=raw,
                                capture_output=True, env=env, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertGreaterEqual(len(result.stdout), 4)
        size = struct.unpack('=I', result.stdout[:4])[0]
        self.assertEqual(size, len(result.stdout) - 4)
        return json.loads(result.stdout[4:])

    def test_download_and_shell_metacharacters_are_passed_as_data(self):
        response = self.exchange({'url': 'https://example.org/video?x=$(touch%20bad);echo'})
        self.assertTrue(response['ok'], response)
        self.assertEqual(Path(response['path']).read_bytes(), b'video fixture')
        self.assertEqual(Path(response['path']).parent, self.home / 'Desktop')
        self.assertEqual(stat.S_IMODE(Path(response['path']).stat().st_mode), 0o600)

    def test_rejects_invalid_inputs_without_downloading(self):
        for value in [None, [], {}, {'url': 1}, {'url': 'file:///etc/passwd'},
                      {'url': 'javascript:alert(1)'}, {'url': 'https://u:p@example.org'},
                      {'url': 'https://'}, {'url': 'https://example.org/\nfoo'}]:
            with self.subTest(value=value):
                self.assertFalse(self.exchange(value)['ok'])
        self.assertFalse((self.home / 'Desktop/test-video.mp4').exists())

    def test_downloader_failure_is_returned(self):
        result = self.exchange({'url': 'https://example.org/unsupported'})
        self.assertFalse(result['ok'])
        self.assertIn('Unsupported URL', result['error'])

    def test_missing_ffmpeg_is_reported_before_download(self):
        # Keep only the fixture bin directory so system FFmpeg cannot mask it.
        (self.home / '.local/bin/ffmpeg').unlink()
        payload = json.dumps({'url': 'https://example.org/video'}).encode()
        result = subprocess.run([sys.executable, str(HOST)],
                                input=struct.pack('=I', len(payload)) + payload,
                                capture_output=True, timeout=10,
                                env=dict(os.environ, HOME=str(self.home),
                                         PATH=str(self.home / '.local/bin')))
        response = json.loads(result.stdout[4:])
        self.assertFalse(response['ok'])
        self.assertIn('FFmpeg is missing', response['error'])
        self.assertFalse((self.home / 'Desktop/test-video.mp4').exists())

    def test_malformed_and_oversized_frames(self):
        for raw in [b'xx', struct.pack('=I', 70000), struct.pack('=I', 2) + b'{x',
                    struct.pack('=I', 10) + b'{}']:
            with self.subTest(raw=raw):
                self.assertFalse(self.exchange(raw=raw)['ok'])

    def test_transcription_missing_engine_does_not_download(self):
        result = self.exchange({'url': 'https://example.org/video', 'transcribe': True})
        self.assertFalse(result['ok'])
        self.assertIn('--transcription', result['error'])
        self.assertFalse((self.home / 'Desktop/test-video.mp4').exists())

    def test_transcription_dispatch_returns_files_and_keeps_video_on_failure(self):
        target = self.home / '.local/share/video-downloader-firefox'
        (target / 'venv/bin').mkdir(parents=True)
        (target / 'venv/bin/python').symlink_to(sys.executable)
        worker = target / 'transcribe.py'
        worker.write_text('''import json, sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.with_suffix('.transcript.txt')
s = p.with_suffix('.srt')
t.write_text('Hello world.\\n')
s.write_text('1\\n00:00:00,000 --> 00:00:01,000\\nHello world.\\n')
print(json.dumps({'transcript': str(t), 'subtitles': str(s)}))
''')
        result = self.exchange({'url': 'https://example.org/video', 'transcribe': True})
        self.assertTrue(result['ok'], result)
        self.assertEqual(Path(result['transcript']).read_text(), 'Hello world.\n')
        self.assertTrue(Path(result['subtitles']).is_file())
        worker.write_text("import sys; print('No audio stream', file=sys.stderr); sys.exit(1)")
        result = self.exchange({'url': 'https://example.org/video', 'transcribe': True})
        self.assertFalse(result['ok'])
        self.assertIn('No audio stream', result['error'])
        self.assertTrue((self.home / 'Desktop/test-video.mp4').exists())

    def test_rejects_nonboolean_transcription_option(self):
        result = self.exchange({'url': 'https://example.org/video', 'transcribe': 'yes'})
        self.assertFalse(result['ok'])
        self.assertFalse((self.home / 'Desktop/test-video.mp4').exists())

    def test_x_login_and_feed_urls_explain_how_to_select_a_post(self):
        for url in [
            'https://x.com/i/jf/onboarding/web?redirect_after_login=%2Fi%2Ftimeline&mode=login',
            'https://x.com/home', 'https://twitter.com/i/flow/login',
        ]:
            with self.subTest(url=url):
                result = self.exchange({'url': url})
                self.assertFalse(result['ok'])
                self.assertIn('individual post', result['error'])
                self.assertIn('timestamp', result['error'])
        self.assertFalse((self.home / 'Desktop/test-video.mp4').exists())

    def test_x_post_urls_are_accepted(self):
        for url in ['https://x.com/i/status/1234567890123456789',
                    'https://x.com/user/status/1234567890123456789/video/1',
                    'https://twitter.com/user/status/1234567890123456789']:
            with self.subTest(url=url):
                self.assertTrue(self.exchange({'url': url})['ok'])


if __name__ == '__main__':
    unittest.main()
