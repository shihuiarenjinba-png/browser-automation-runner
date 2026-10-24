# Browser Automation Runner — runFullTrust justification draft

The package contains a packaged Win32 desktop application and launches the bundled Playwright/Chromium runtime as part of user-approved browser workflows. `runFullTrust` is required for the desktop executable to start the local browser process and save user-requested screenshots or downloads within the configured local root directory.

The app does not request administrator elevation and does not use this capability to change Windows security settings or execute arbitrary operating-system commands.
