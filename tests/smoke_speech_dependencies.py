"""Check optional speech dependencies with synthetic data, never a model."""
import importlib.metadata
import io
import tempfile
import wave
from pathlib import Path

import av
import numpy as np
from faster_whisper.audio import decode_audio
from faster_whisper.feature_extractor import FeatureExtractor
from filelock import FileLock, Timeout

sample_rate = 16000
pcm = (np.sin(np.arange(sample_rate) * 2 * np.pi * 440 / sample_rate) * 8192).astype("<i2")
wav = io.BytesIO()
with wave.open(wav, "wb") as output:
    output.setnchannels(1)
    output.setsampwidth(2)
    output.setframerate(sample_rate)
    output.writeframes(pcm.tobytes())
wav.seek(0)
audio = decode_audio(wav, sampling_rate=sample_rate)
assert audio.dtype == np.float32 and audio.size == sample_rate
assert np.isfinite(audio).all() and np.max(np.abs(audio)) > 0.2
features = FeatureExtractor()(audio)
assert features.ndim == 2 and features.shape[0] == 80
assert features.shape[1] > 0 and np.isfinite(features).all()

try:
    decode_audio(io.BytesIO(b"not audio"), sampling_rate=sample_rate)
except (av.error.FFmpegError, ValueError):
    pass
else:
    raise AssertionError("Malformed audio was accepted")

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "fixture.lock"
    with FileLock(path, timeout=0):
        try:
            with FileLock(path, timeout=0):
                raise AssertionError("Competing lock was accepted")
        except Timeout:
            pass
    with FileLock(path, timeout=0):
        pass

versions = {name: importlib.metadata.version(name) for name in ("av", "numpy", "filelock")}
print(f"Speech dependency smoke passed: {versions}")
