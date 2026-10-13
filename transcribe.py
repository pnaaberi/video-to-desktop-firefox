"""Local speech recognition worker; stdout contains only the result JSON."""
import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile


def timestamp(seconds):
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}'


def save_transcript(video, segments):
    text = video.with_suffix('.transcript.txt')
    subtitles = video.with_suffix('.srt')
    result = {'transcript': str(text), 'subtitles': str(subtitles)}
    if text.is_file() and subtitles.is_file():
        return result
    if text.exists() or subtitles.exists():
        raise ValueError('A transcript output already exists. Move it aside before trying again.')
    # Stage results so decoding failures never leave incomplete transcripts.
    with tempfile.TemporaryDirectory(prefix='.transcribe-', dir=video.parent) as directory:
        staged_text = Path(directory) / 'text'
        staged_srt = Path(directory) / 'srt'
        count = 0
        with staged_text.open('w', encoding='utf-8') as txt, staged_srt.open('w', encoding='utf-8') as srt:
            for segment in segments:
                words = segment.text.strip()
                if not words:
                    continue
                count += 1
                txt.write(words + '\n')
                srt.write(f'{count}\n{timestamp(segment.start)} --> {timestamp(segment.end)}\n{words}\n\n')
        if not count:
            raise ValueError('No speech was detected in this video.')
        staged_text.chmod(0o600)
        staged_srt.chmod(0o600)
        # Hard links publish without overwriting an existing file.
        os.link(staged_text, text)
        try:
            os.link(staged_srt, subtitles)
        except OSError:
            text.unlink()
            raise
    return result


def main():
    try:
        video = Path(sys.argv[1]).resolve()
        model_path = Path(__file__).resolve().parent / 'models/base'
        with contextlib.redirect_stdout(sys.stderr):
            from faster_whisper import WhisperModel
            model = WhisperModel(str(model_path), device='cpu', compute_type='int8',
                                 cpu_threads=min(4, os.cpu_count() or 1), local_files_only=True)
            segments, _ = model.transcribe(str(video), beam_size=5, vad_filter=True)
            result = save_transcript(video, segments)
        print(json.dumps(result))
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
