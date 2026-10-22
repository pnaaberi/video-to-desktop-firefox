# Video to Desktop maintenance

- Read this file, README.md and docs/DEVELOPMENT.md before changes; verify ownership and a clean Git baseline.
- Preserve Linux/Firefox scope, native-host ID/allowlist, HTTP(S) URL validation, shell-free subprocesses, no-overwrite behavior and owner-only outputs.
- Do not import browser cookies, add broad site permissions or upload media/transcripts. Keep models, downloads, transcripts and audit evidence out of Git.
- Use synthetic tests; never install/register the real helper, write to Desktop, fetch a real video or download a speech model merely to run routine checks.
- Run the documented Python/Node tests and package check. Speech dependency updates need resolver/import/audio-decoder and invalid-input checks on supported Python 3.11/3.12 without a model download.
- Keep dependency pins and affected developer/maintenance notes current. Preserve unsigned-package and Mozilla-signing boundaries; a build is not signing or distribution.
- Publish only scoped, reviewed source with public-handle/noreply metadata, and preserve existing deployment/runtime ownership.
