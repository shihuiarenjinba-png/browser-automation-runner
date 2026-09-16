$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'build dependency installation failed.' }

python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'unit/UI language tests failed.' }

python -m PyInstaller --clean --noconfirm --onefile --windowed --name BrowserAutomationRunner --collect-all playwright desktop_app.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

Write-Host 'Built BrowserAutomationRunner.exe code package after regression and language tests passed.'
Write-Host 'IMPORTANT: this does not by itself prove that the validated Chromium runtime is bundled for commercial distribution.'
Write-Host 'Before sale: complete SALES_RELEASE_CHECKLIST.md, including Playwright/Chromium packaging and controlled browser smoke tests.'
