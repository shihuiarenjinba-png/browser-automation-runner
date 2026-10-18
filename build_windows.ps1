$ErrorActionPreference = 'Stop'

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'build dependency installation failed.' }

python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'unit/UI language tests failed.' }

$stamp = [guid]::NewGuid().ToString("N")
$dest = Join-Path $PSScriptRoot ("dist-validation\\BrowserAutomationRunner-" + $stamp)
$work = Join-Path $env:TEMP ("BrowserAutomationRunner-work-" + $stamp)
$spec = Join-Path $env:TEMP ("BrowserAutomationRunner-spec-" + $stamp)
if (Test-Path -LiteralPath $dest) { throw "Validation output already exists" }

python -m PyInstaller --clean --noconfirm --onefile --windowed --name BrowserAutomationRunner --distpath "$dest" --workpath "$work" --specpath "$spec" --add-data "workflow.example.json;." --collect-all playwright desktop_app.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
# Build a self-contained directory distribution: browser executable and
# Playwright browser assets live next to the frozen EXE, never in user cache.
$browserPath = Join-Path $dest "pw-browsers"
$env:PLAYWRIGHT_BROWSERS_PATH = $browserPath
python -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw 'Playwright Chromium download/install failed.' }
if (-not (Test-Path -LiteralPath $browserPath -PathType Container)) {
    throw "No bundled browser runtime directory produced: $browserPath"
}
$browserExecutables = @(Get-ChildItem -LiteralPath $browserPath -Filter "chrome*.exe" -File -Recurse -ErrorAction Stop)
if ($browserExecutables.Count -lt 1) { throw 'Bundled Chromium executable not found.' }

$exePath = Join-Path $dest "BrowserAutomationRunner.exe"
if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) { throw "Wrong EXE entrypoint: $exePath" }
$process = Start-Process -FilePath $exePath -ArgumentList "--self-test" -PassThru -Wait
if ($process.ExitCode -ne 0) { throw "Frozen EXE no-network self-test failed: $($process.ExitCode)" }
$smoke = Start-Process -FilePath $exePath -ArgumentList "--browser-smoke" -PassThru -Wait
if ($smoke.ExitCode -ne 0) { throw "Frozen EXE bundled Chromium offline smoke failed: $($smoke.ExitCode)" }
$sha = (Get-FileHash -LiteralPath $exePath -Algorithm SHA256).Hash.ToLowerInvariant()
$report = [ordered]@{
    exe = "BrowserAutomationRunner.exe"
    source_entrypoint = "desktop_app.py"
    sha256 = $sha
    packaged_no_network_self_test = "PASS"
    packaged_chromium_offline_smoke = "PASS"
    chromium_runtime_directory = "pw-browsers"
    chromium_exe_count = $browserExecutables.Count
    interactive_windows_qa = $false
    microsoft_store_certified = $false
    signed = $false
    sale_approved = $false
}
$report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dest "validation-manifest.json") -Encoding UTF8
Write-Host "NON-SALES validation EXE: $exePath; SHA256: $sha"


Write-Host 'Built BrowserAutomationRunner.exe code package after regression and language tests passed.'
Write-Host 'Validation directory includes adjacent Chromium runtime and offline launch smoke; full browser, license and MSIX acceptance remain HOLD.'
Write-Host 'Before sale: complete SALES_RELEASE_CHECKLIST.md, including Playwright/Chromium packaging and controlled browser smoke tests.'
