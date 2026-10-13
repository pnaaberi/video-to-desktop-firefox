# Video to Desktop — Firefox extension

Download videos from sites supported by yt-dlp, including X, and direct HTTP(S)
video links. Downloads save to your Desktop at best available quality, preferring
MP4, with audio when available. Existing files are not overwritten. Only one job
runs at a time; playlist URLs are limited to one item.

## Load it in Firefox

First install the native helper using the instructions below.

1. Open `about:debugging#/runtime/this-firefox` in Firefox.
2. Click **Load Temporary Add-on…**.
3. Select `extension/manifest.json` in this folder (or the unsigned XPI from Releases).
4. Open a video page and click **Video to Desktop** in the extensions menu.
   Pin it to the toolbar for easy access. You can also right-click a video,
   video link, or page and select **Download video to Desktop**.

For speech transcription, right-click the video page/link/video and choose
**Download + transcribe to Desktop**. This saves the video plus a
`.transcript.txt` text file and `.srt` timestamped subtitles beside it.
Transcription uses the local multilingual Whisper base model with automatic
language detection; it preserves the spoken language instead of translating.
Speech recognition can make mistakes, especially with music, overlapping voices,
or unusual names. Processing long videos can take time. The badge stays ↓ until
both downloading and transcription finish. The toolbar click remains video-only.

Install the local engine and model with `python3 install.py --transcription`. Existing
transcript/subtitle pairs are reused without overwriting them. If transcription
fails, the saved video remains on Desktop and the notification reports the error.

On X, open an individual post by clicking its timestamp, then run the action.
You can also right-click the post timestamp link directly. X login screens and
the home feed are not video URLs. If X redirects you to login, use the post's
original link through the right-click link menu instead. Some restricted posts
still require authentication and may not download.
Firefox may group both actions under a **Video to Desktop** context submenu.

The badge shows ↓ while downloading, OK after saving, or ! on failure.
Hover over the toolbar button for the saved path or error; notifications also
report the result. Keep Firefox open until downloads finish. These downloads
are handled by yt-dlp and do not appear in Firefox's built-in download manager.

Temporary add-ons are removed when Firefox restarts; load it again afterward.
Permanent installation in regular Firefox requires Mozilla signing. The XPI is
unsigned; opening it as a regular add-on installation will be rejected.
Submit the extension ZIP for an unlisted signed add-on at
https://addons.mozilla.org/developers/ if you want persistent installation.
No signature checks or browser security settings have been changed.

## Install the helper on Linux

Install Python 3.9 or later, a current yt-dlp, and FFmpeg, then run from this repository:

```bash
python3 install.py
```

For transcription, install Python 3.11 or 3.12 and run:

```bash
python3 install.py --transcription
```

This creates an isolated Python environment, installs the pinned packages in
`requirements-transcription.txt`, and downloads faster-whisper's base model.
Python 3.11 is preferred, with 3.12 as a fallback for binary package compatibility.
After setup, speech processing runs locally without network access or API keys.
No audio is uploaded. Downloading videos still contacts their original provider.
The model and isolated environment live alongside the helper in
`~/.local/share/video-downloader-firefox/`.

The helper lives in `~/.local/share/video-downloader-firefox/host.py`; Firefox's
registration is `~/.mozilla/native-messaging-hosts/video_downloader.json`.
No root privileges or background server are needed. Sandboxed Flatpak/Snap
Firefox may require additional host integration; this package targets native
Linux Firefox.

## Limits and privacy

Support depends on yt-dlp's current extractors. DRM-protected media, some sites
requiring authentication, and arbitrary embedded players may not work. Try the
video's own page instead of a feed page if extraction fails. Blob video URLs
fall back to their page URL. This extension does not inspect page contents,
cookies, history, or stored logins. It sends the explicitly selected URL to the
local helper; yt-dlp contacts the video provider to retrieve it. It ignores
existing yt-dlp configuration for predictable behavior.
User-installed yt-dlp plugins are disabled. New video and transcript files are
created with owner-only permissions on Linux. Existing files retain their
permissions. Desktop notifications display local filenames/paths and error
details, which can include the selected URL; configure your desktop's notification
privacy settings if those should not appear on a lock screen.

To uninstall the helper, delete the two helper paths above. Remove the add-on
through Firefox's extensions settings.

To remove the transcription environment and model too, delete the entire
`~/.local/share/video-downloader-firefox/` directory.

## Verification

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_background.cjs
```

Optional live Firefox integration test (downloads the URL you explicitly supply):

```bash
python3 tests/smoke_firefox.py 'https://example.org/your-video' --transcribe
```

It requires Firefox and npm's `npx` command and runs a temporary headless browser
profile. It does not alter the normal browser profile. The test uses a temporary
localhost result callback which is excluded from the extension package.

Only the `extension/` contents are packaged in the XPI/ZIP. Python helpers,
third-party programs and model weights are installed separately.
See [LICENSE](LICENSE) and [third-party acknowledgements](THIRD_PARTY.md).

Build unsigned XPI/ZIP packages (includes the license and acknowledgements):

```bash
python3 scripts/package.py
```

The generated files are in `dist/`. They can be temporarily loaded in Firefox
or submitted for Mozilla signing. No downloaded media or runtime data is bundled.
