# Browser Automation Runner — QA handoff and release gates

**Status: HOLD.** Browser engine is an advanced fallback, not a general AI agent.

## Improvements (2026-10-18)
- Screenshots and downloads are written into unique temporary files, then
  atomically published. With overwrite=false, a simultaneous writer wins and
  its existing file is not overwritten.
- Running a real browser requires a Dry Run for the **exact unchanged workflow
  JSON and source path**. Approval is consumed at live start before browser
  side effects, even if the eventual result is uncertain.
- Cancelling the final warning preserves preview status; changing a workflow
  action, host, output or selected JSON invalidates it.
- Language changes and file selection are blocked during live execution.
- The GUI explains the limited Dry Run (configuration and host check, NOT
  actual navigation) and three-step first-use workflow.

### Operator commands (Windows)
```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m playwright install chromium
python desktop_app.py
```
Tests to add/perform on a **controlled local/offline HTTPS fixture**:
launch packaged Chromium from an EXE installation; cross-host popup/iframe;
blocked subresources; symlink, junction, network-share/OneDrive output collision;
download timeout, interruption and cleanup; 100%,125%,150% DPI, keyboard
accessibility, errors and language preservation.

**Crucial packaging gate:** PyInstaller EXE currently packages application
code, but does NOT prove that the pinned Chromium browser runtime is included,
installed, licensed/noticed, or can run on a clean Windows machine. No signed
Store-ready MSIX is available. Do not create a Store product slot on the
assumption this is ready.

**GitHub CI blocker:** Windows/Ubuntu jobs on this branch fail before steps
are recorded and logs are not obtainable. Neither code failure nor PASS has
been demonstrated. Code operator must investigate account-level Actions
settings/quota/policy, then run the full matrix and real-browser smoke.
