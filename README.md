# Video to Desktop for Firefox

Save videos supported by yt-dlp to your Desktop. Optionally transcribe their
speech locally and save a text transcript plus timestamped SRT subtitles.

**Current releases are unsigned.** Load them through Firefox's `about:debugging`.
They disappear after a browser restart; permanent installation requires Mozilla signing.

[Download the add-on](https://github.com/pnaaberi/video-to-desktop-firefox/releases/latest)
· [Troubleshooting](docs/TROUBLESHOOTING.md)
· [Development and packaging](docs/DEVELOPMENT.md)

## Requirements

| Component | Requirement |
| --- | --- |
| Platform | Native desktop Firefox on Linux; tested on x86-64 Linux |
| Firefox | 142 or later |
| Native helper | Python 3.9 or later |
| Downloads | Current yt-dlp and FFmpeg on PATH or in `~/.local/bin` |
| Transcription setup | Python 3.11 or 3.12 with venv support; internet for installation |
| Transcription processing | CPU and the local multilingual Whisper base model; no GPU or API key |

These instructions do not support Windows, macOS, Android, or sandboxed
Flatpak/Snap Firefox. The model is approximately 142 MiB; Python packages need
additional disk space. Long recordings can take time to process.

## Install

### 1. Install prerequisites

Use your distribution's package manager to install Python, FFmpeg, and Git.
For transcription, also install Python 3.11 or 3.12 and its venv support.
Install current yt-dlp through your package manager, or through
[pipx](https://github.com/pypa/pipx) if pipx is installed:

```bash
pipx install yt-dlp
pipx ensurepath
```

Open a new terminal after `pipx ensurepath`. Check prerequisites:

```bash
python3 --version
ffmpeg -version
yt-dlp --version
```

For transcription, `python3.11 --version` or `python3.12 --version` must work.
A newer system Python alone does not satisfy the transcription installer's requirement.

### 2. Install the local helper

The extension needs this helper to run yt-dlp. The XPI alone is insufficient.

```bash
git clone https://github.com/pnaaberi/video-to-desktop-firefox.git
cd video-to-desktop-firefox
python3 install.py
```

For video **and transcription**, replace the last command with:

```bash
python3 install.py --transcription
```

This installs the helper, creates an isolated Python environment, installs pinned
speech dependencies, and downloads the model. Wait for setup to finish. Success
prints `Installed native helper:` followed by the registration path. Run the
installer as your normal user, without `sudo`.

Without Git, choose **Code → Download ZIP** on the repository, extract it, and
run the installer from the extracted folder. The release extension ZIP contains
only the add-on; the source archive contains the helper and installer too.

### 3. Load the extension

1. In Firefox's address bar, enter `about:debugging#/runtime/this-firefox`.
2. Click **Load Temporary Add-on…**.
3. Select `extension/manifest.json` inside the source folder, or select the `.xpi`
   downloaded from this repository's Releases page.
4. Find **Video to Desktop** in Firefox's extensions menu. Pin it to the toolbar
   for one-click video downloads.

Opening an unsigned XPI as an ordinary add-on installation will fail. Use the
**Load Temporary Add-on…** button. See Mozilla's
[temporary installation instructions](https://extensionworkshop.com/documentation/develop/temporary-installation-in-firefox/).

## Download a video

1. Open the video's own page, rather than a home feed or login page.
2. Click the **Video to Desktop** toolbar button.
3. Keep Firefox open until the badge shows **OK** or a completion notification appears.
4. Find the video on your Desktop.

Alternatively, right-click a video, a video link, or an empty area of its page.
Choose **Video to Desktop → Download video to Desktop**. If Firefox shows the
extension's actions directly, select the action without opening a submenu.

## Download and transcribe

1. Complete setup with `python3 install.py --transcription`.
2. Open the video's own page.
3. Right-click its video, a video link, or an empty area of the page.
4. Choose **Video to Desktop → Download + transcribe to Desktop**.
5. Keep Firefox open until the operation finishes.

The toolbar click downloads video only; use the right-click action to transcribe.
Three files are saved together:

| Example filename | Contents |
| --- | --- |
| `Example-video-123456789.mp4` | Video with audio, when available |
| `Example-video-123456789.transcript.txt` | UTF-8 transcript to open in a text editor |
| `Example-video-123456789.srt` | Timestamped subtitles for a compatible media player |

Whisper detects the language and retains the spoken language; it does not translate.
It can make mistakes with names, music, overlapping speakers, or unclear speech.
Review transcripts before relying on them. If transcription fails or no speech is
detected, the downloaded video remains on Desktop.

### On X

Click a post's timestamp to open the individual post, then use the action. Its
address should contain `/status/`, rather than `/home` or a login/onboarding path.
You can also right-click the timestamp link directly and choose the action.
This sends the original post URL if opening the page redirects to login.
Restricted posts can still require authentication.

## Status and output

| Badge | Meaning |
| --- | --- |
| **↓** | Downloading, or downloading and transcribing |
| **OK** | Files saved; hover over the button to see their paths |
| **!** | Failed; hover over the button or read the notification for the error |

Files go to the Desktop returned by `xdg-user-dir DESKTOP`, falling back to
`~/Desktop`. These operations do not appear in Firefox's built-in download list.
One operation runs at a time. There is no pause/cancel control. Closing Firefox
can interrupt a job. Playlist URLs are limited to their first item.

Existing videos are not overwritten. Complete transcript/subtitle pairs are reused;
if only one exists, move it aside before retrying. Downloads prefer MP4 and merge
audio when available. DRM, login-restricted videos, and some embedded players
may not work; support depends on yt-dlp's extractors.

## Privacy and permissions

Only the URL explicitly selected is sent to the local helper. The extension does
not read browser cookies, stored logins, browsing history, or page text. It does
not automatically reuse your signed-in browser session. yt-dlp contacts the video
provider. Transcription uses local cached model files; no audio is uploaded.
Setup downloads packages from PyPI and the model from Hugging Face.

Permissions are `activeTab`, `menus`, `nativeMessaging`, and `notifications`.
There are no broad site permissions or production local web server. The native
host accepts this add-on's ID only. It validates HTTP(S) URLs and runs yt-dlp
without a shell, user configuration, or user-installed plugins.

New videos and transcripts have owner-only permissions on Linux. Existing files
keep their current permissions. Notifications can show filenames, local paths,
and errors containing the selected URL; consider lock-screen notification settings.
Media, transcripts and raw audit reports are excluded from repository/release files.

## Update

From the source folder, when no job is running:

```bash
git pull --ff-only
python3 install.py
```

Use `python3 install.py --transcription` to update the full transcription setup.
If yt-dlp was installed through pipx, update it with `pipx upgrade yt-dlp`;
otherwise use its original installation method.

For an extension loaded from source, click **Reload** in `about:debugging`.
For a packaged XPI, remove the previous temporary add-on and load the newer XPI.
Reload temporary add-ons after every Firefox restart. For permanent installation,
see [Mozilla signing](docs/DEVELOPMENT.md#mozilla-signing).

## Uninstall

Remove the add-on through Firefox's extensions settings or `about:debugging`.
To remove this project's installed helper, environment, and model:

```bash
rm -f "$HOME/.mozilla/native-messaging-hosts/video_downloader.json"
rm -rf "$HOME/.local/share/video-downloader-firefox"
```

Downloaded videos/transcripts and your source checkout remain untouched.
No root privileges or background service are used by the helper.

## More information

- [Troubleshooting and safe issue reports](docs/TROUBLESHOOTING.md)
- [Developer tests, packaging, and signing](docs/DEVELOPMENT.md)
- [MIT license](LICENSE) and [third-party acknowledgements](THIRD_PARTY.md)
