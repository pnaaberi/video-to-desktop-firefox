# Changelog

## Unreleased

- Maintenance: update FileLock to 4.2.0 and NumPy to 2.5.4 on Python 3.12+, retaining tested NumPy 2.4.6 on Python 3.11. Keep PyAV 18.1.0: the proposed 19.0.1 rejects Python 3.11 and breaks Faster Whisper's decoder on Python 3.12.
- Add isolated resolver/audit/decoder/feature/locking smoke coverage for Python 3.11 and 3.12 without models or real media. Run CI on PRs/main or explicit dispatch rather than duplicating the speech matrix for each feature push. Native-host permissions, add-on ID and extension package content are unchanged.
