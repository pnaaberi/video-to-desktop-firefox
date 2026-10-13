import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import os
import stat


class TranscriptTests(unittest.TestCase):
    def module(self):
        path = Path(__file__).resolve().parents[1] / 'transcribe.py'
        self.assertTrue(path.is_file(), 'The transcription worker has not been implemented')
        spec = importlib.util.spec_from_file_location('transcribe', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_writes_text_and_normalized_srt_timestamps_without_overwrites(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'video.mp4'
            segments = [SimpleNamespace(start=59.9996, end=3601.234, text=' Hei maailma. ')]
            previous = os.umask(0o022)
            try:
                result = module.save_transcript(path, iter(segments))
            finally:
                os.umask(previous)
            for filename in result.values():
                self.assertEqual(stat.S_IMODE(Path(filename).stat().st_mode), 0o600)
            self.assertEqual(Path(result['transcript']).read_text(), 'Hei maailma.\n')
            self.assertEqual(Path(result['subtitles']).read_text(),
                             '1\n00:01:00,000 --> 01:00:01,234\nHei maailma.\n\n')
            module.save_transcript(path, iter([SimpleNamespace(start=0, end=1, text='changed')]))
            self.assertEqual(Path(result['transcript']).read_text(), 'Hei maailma.\n')

    def test_empty_speech_and_failed_generator_leave_no_transcript_files(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'video.mp4'
            with self.assertRaisesRegex(ValueError, 'speech'):
                module.save_transcript(path, iter([]))
            def broken():
                yield SimpleNamespace(start=0, end=1, text='hello')
                raise ValueError('audio decoding failed')
            with self.assertRaisesRegex(ValueError, 'audio decoding'):
                module.save_transcript(path, broken())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_partial_existing_outputs_are_preserved(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'video.mp4'
            text = path.with_suffix('.transcript.txt')
            text.write_text('My own transcript')
            with self.assertRaisesRegex(ValueError, 'exists'):
                module.save_transcript(path, iter([]))
            self.assertEqual(text.read_text(), 'My own transcript')


if __name__ == '__main__':
    unittest.main()
