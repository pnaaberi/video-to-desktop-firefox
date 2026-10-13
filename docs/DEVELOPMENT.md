# Development and packaging

## Components

| File | Responsibility |
| --- | --- |
| `extension/manifest.json` | Add-on ID/version, minimum Firefox version, permissions |
| `extension/background.js` | Toolbar/menu actions, native request, badges/notifications |
| `host.py` | Bounded native framing, URL validation, yt-dlp and speech-worker subprocesses |
| `transcribe.py` | Local Whisper inference and no-overwrite text/SRT output |
| `install.py` | Per-user Linux native-host registration and optional speech setup |
| `requirements-transcription.txt` | Pinned speech dependencies |
| `scripts/package.py` | Reproducible unsigned XPI/ZIP packaging |
| `tests/` | Synthetic checks and optional real Firefox integration test |

Firefox sends the explicitly selected URL and a boolean transcription option to
the helper. The helper downloads one video and optionally runs the speech worker,
then returns saved paths or an error. There are no content scripts or production
localhost server. A speech-worker failure preserves the video.

The ID `video-downloader@local.invalid` must match the installed native manifest's
`allowed_extensions` entry. Changing it requires updating/reinstalling the helper
and reloading the extension.

## Automated checks

Use Python 3.11 and Node.js 22 to match CI. These synthetic checks do not require
a speech model, internet access, or installed FFmpeg/yt-dlp:

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_background.cjs
```

There are currently 13 Python and 6 Node tests covering framing, invalid inputs,
X login-page handling, dependencies/errors, safe command arguments, owner-only
permissions, timestamps, output preservation, menu routing and duplicate clicks.
Browser API boundary tests do not prove every site or notification system works.

With npm/npx installed, validate the extension:

```bash
npx --yes web-ext lint --no-config-discovery --source-dir extension --output text
```

This obtains web-ext through npm; it is a developer check, not a runtime dependency.
CI runs the Python/Node checks and package build with read-only repository
permissions. GitHub Actions are pinned to commit hashes.

## Live Firefox check

Install the helper and prerequisites first. Supply a short public video you are
allowed to download (replace the example URL):

```bash
python3 tests/smoke_firefox.py 'https://example.org/your-video'
python3 tests/smoke_firefox.py 'https://example.org/your-video' --transcribe
```

The second command requires completed transcription setup. The script expects
native Firefox at `/usr/bin/firefox` and `npx` on PATH. It uses a temporary headless
profile, the installed helper, and real Desktop downloads. It waits up to 55
seconds, so choose a short clip. Your normal Firefox profile is not changed.
A test-only localhost permission/callback is added to a copied extension and is
never included in packages. Manually check menus, notifications and media/subtitle
playback separately when changing them.

## Build packages

```bash
python3 scripts/package.py
```

The version is read from `extension/manifest.json`. Outputs are
`dist/video-to-desktop-<version>.xpi` and `dist/video-to-desktop-<version>.zip`;
they contain identical ZIP bytes. Contents are the manifest, background script,
SVG icon, MIT license and third-party acknowledgements. Timestamps and permissions
are fixed for reproducible metadata. Helpers, models, dependencies, media,
transcripts, logs and audit reports are excluded.

Load the XPI temporarily through `about:debugging`, or submit the ZIP for signing.
GitHub's source archive is different: it also contains the installer and helpers.

## Mozilla signing

No current release package is signed. For permanent regular-Firefox installation:

1. Build the extension ZIP with `python3 scripts/package.py`.
2. Sign in to the [Mozilla Add-on Developer Hub](https://addons.mozilla.org/developers/).
3. Submit a new add-on, choosing self-distribution/unlisted if you do not want an
   AMO listing. Upload the built extension ZIP and complete Mozilla's requested
   review and privacy declarations.
4. After signing, distribute the signed XPI. Users still need to install the
   Linux helper separately.

See Mozilla's [signing and distribution overview](https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/).
Keep the add-on ID unchanged for helper compatibility. Building the archive does
not submit anything to Mozilla. Do not publish signing credentials or weaken
browser signature checks as a substitute for signing.

## Publication checks

Audit the exact outgoing commits and archives for secrets, private URLs, local
paths, author/committer metadata, runtime files and licensing issues. Use a public
handle and GitHub noreply identity. Raw audit reports belong outside the repository.
Run appropriate checks and scan the resolved dependency graph for known advisories.

Preserve owner-only output permissions, URL validation, native-host allowlisting,
safe command arguments, no-overwrite behavior and local-only transcription.
Advisory checks are point-in-time; keep external tools and speech dependencies current.
