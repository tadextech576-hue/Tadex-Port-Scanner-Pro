# Tadex Port Scanner Pro

An Android/Kivy app with a real TCP connect scanner.

## Safety
Use this tool only against devices, servers, and networks you own or have explicit permission to assess. It performs TCP connection attempts; it is not a stealth scanner and does not exploit services.

## Features
- Resolve an IPv4 hostname or accept an IPv4 address.
- Scan a chosen TCP port range (1–65535).
- Real socket connection tests, not generated results.
- Open, closed, timeout/no-response, and connection-error statuses.
- Adjustable timeout and worker count.
- Live progress and stop control.
- Export CSV and JSON reports.
- Android APK build using GitHub Actions.

## Build the Android APK
1. Open the repository's Actions tab.
2. Select Build Tadex Android APK.
3. Press Run workflow (or push a commit to main).
4. Wait for the workflow to finish successfully.
5. Open the completed workflow run and scroll to Artifacts.
6. Download tadex-port-scanner-debug-apk, extract the ZIP, and install the APK.
7. If Android asks, allow installation from your browser or file manager.

The first Android build can take a while because Buildozer downloads the Android toolchain. GitHub Actions stores the APK as a workflow artifact; it does not automatically publish a public release.

## Run on a computer with Python
Install Python 3, then run:
    python -m pip install -r requirements.txt
    python main.py

On Android, use the APK produced by the workflow. Termux can run the scanner engine independently, but Kivy Android packaging is handled by the GitHub Actions Linux runner.

## Files
- main.py — Kivy interface and export functions.
- scanner.py — TCP scanning engine.
- requirements.txt — Python dependencies.
- buildozer.spec — Android packaging configuration.
- .github/workflows/build-apk.yml — automated APK build.

## Limitations
This is a TCP connect scanner. UDP scanning, OS fingerprinting, vulnerability exploitation, and guaranteed service/version detection are not included. A timeout means no response within the selected time; it does not prove a firewall is present.
