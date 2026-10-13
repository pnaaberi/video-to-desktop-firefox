# Troubleshooting

Run terminal commands from the source repository folder. Hover over the toolbar
button for the latest error, or read its desktop notification.

| Problem | What to do |
| --- | --- |
| No transcription action | Right-click inside the webpage, then open **Video to Desktop**. Select **Download + transcribe to Desktop**. The toolbar click downloads video only. |
| No extension/menu after restarting Firefox | Open `about:debugging#/runtime/this-firefox` and load `extension/manifest.json` or the release XPI using **Load Temporary Add-on…**. |
| Unsigned XPI / could not be verified | Use temporary loading through `about:debugging`. Opening the XPI as an ordinary installation fails. Permanent normal-Firefox installation requires Mozilla signing. |
| Local helper unavailable / No such native application | Run `python3 install.py` as the Linux user who runs Firefox. For transcription, run it with `--transcription`. Native Linux Firefox is required; sandboxed editions need additional integration. |
| yt-dlp or FFmpeg missing | Check `yt-dlp --version` and `ffmpeg -version`; install missing tools. The helper checks `~/.local/bin` and Firefox's inherited PATH. |
| yt-dlp older than 90 days | Update through its original installation method; use `pipx upgrade yt-dlp` for a pipx install. A warning alone does not mean the download failed. |
| Unsupported URL | Open the individual video page or right-click its link. A home feed, profile, or login screen is not the video's URL. Update yt-dlp, then retry a supported public video. |
| Transcription not installed | Install Python 3.11/3.12 with venv support, then run `python3 install.py --transcription` and allow setup/model downloads to finish. |
| Model cannot load | Rerun the full transcription installer. Inference uses local model files and will not silently download a missing model. |
| No speech / decoding error | Check that the saved video plays and has audible speech. Silence, music, missing audio, or corrupt/unsupported media may fail. The video remains saved. |
| Only one transcript output exists | Move the existing `.transcript.txt` or `.srt` to a safe backup location, then retry. Existing complete pairs are reused; move both aside to regenerate them. |
| No notification | Check the badge/hover text and Desktop folder. OS notification settings may hide messages. |
| Job seems slow | Keep Firefox open and wait. One job runs at a time; long CPU transcription can take time. There is no percentage, pause, or cancel control. Each stage times out after six hours. |

## X login and feed pages

On X, click a post's timestamp so the address contains `/status/`. If the page
redirects to login, right-click the timestamp link and use the extension on that
link directly. Addresses containing `/i/jf/onboarding/`, `/i/flow/login`, or `/home`
are not individual videos. Updating yt-dlp cannot make a login page downloadable.
The extension does not import cookies, so a signed-in browser tab does not
necessarily make restricted content accessible to yt-dlp.

A `blob:` video source falls back to its containing page URL. Use the video's own
page rather than a feed containing several videos. DRM media remains unsupported.

## Check the helper installation

```bash
test -f "$HOME/.mozilla/native-messaging-hosts/video_downloader.json"
test -x "$HOME/.local/share/video-downloader-firefox/host.py"
```

Both commands should exit successfully after installation. The installed helper
and optional speech environment/model are in
`~/.local/share/video-downloader-firefox/`. Retry the installer if setup failed;
`python3 install.py` alone does not install transcription dependencies.

To locate your configured Desktop:

```bash
xdg-user-dir DESKTOP
```

When this command is unavailable, the helper uses `~/Desktop`. Downloads are
handled by yt-dlp, so Firefox's built-in download manager stays empty.

## Reporting problems safely

Use the repository's [Issues page](https://github.com/pnaaberi/video-to-desktop-firefox/issues)
for ordinary problems. Include your OS, native vs. sandboxed Firefox, Firefox
version, `yt-dlp --version`, the action chosen, and a redacted error message.
Do not publish cookies, login tokens, private video links, signed URL query strings,
personal local paths, transcripts, or audio. Use a public reproducible example
when possible. For security issues, use GitHub's private vulnerability reporting
option if available; do not post confidential details or exploits publicly.
