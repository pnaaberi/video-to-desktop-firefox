# External dependencies

Original extension/helper code and the SVG icon are licensed under the MIT
license in LICENSE. Third-party executables, packages and model weights are
installed separately and are not bundled in this repository or extension XPI.
Their own licenses remain applicable.

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Unlicense for upstream source;
  separately distributed builds can include components with other licenses.
- [FFmpeg](https://ffmpeg.org/legal.html): LGPL or GPL depending on build options.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): MIT, SYSTRAN.
- [Whisper](https://github.com/openai/whisper): MIT, OpenAI.
- [Converted multilingual base model](https://huggingface.co/Systran/faster-whisper-base):
  distributed separately by SYSTRAN with its upstream model license.
- [CTranslate2](https://github.com/OpenNMT/CTranslate2): MIT, OpenNMT.
- [PyAV](https://github.com/PyAV-Org/PyAV): BSD-3-Clause; binary wheels contain
  separately licensed media libraries.

The installer resolves the packages pinned in requirements-transcription.txt.
Dependency distributions carry their own license and notice files. No downloaded
video, audio, transcript or user media is included in the repository or package.
