# Run the student app on an Android emulator (Windows)

Checked on this laptop: 15 GB RAM, 129 GB free on C:, CPU virtualization ON, VS Code 1.146 installed.
Missing: Android Studio + Android SDK, and the Flutter extension for VS Code.

Total download: about 4–6 GB. Time: about 45–60 minutes the first time.

---

## Part A — Install Android Studio (gives you the SDK and the emulator)

1. Download **Android Studio** from the official site: https://developer.android.com/studio
2. Run the installer. Keep the defaults, and make sure **Android Virtual Device** is ticked.
3. Open Android Studio. In the setup wizard choose **Standard** → **Next** → **Finish**.
   It downloads the Android SDK (a few GB). Wait until it says it is done.
4. On the welcome screen: **More Actions → SDK Manager** → tab **SDK Tools** →
   tick **Android SDK Command-line Tools (latest)** → **Apply** → **OK**.

## Part B — Let Windows run the emulator fast

Windows already has Hyper-V running, so the emulator needs **Windows Hypervisor Platform**.

5. Press Start, type **Turn Windows features on or off**, open it.
6. Tick **Windows Hypervisor Platform** (and leave **Virtual Machine Platform** ticked) → **OK**.
7. **Restart the laptop.**

## Part C — Connect Flutter to Android

8. Open a **new** PowerShell window and accept the Android licences (read them, type `y` for each):
   ```powershell
   flutter doctor --android-licenses
   ```
9. Check everything:
   ```powershell
   flutter doctor
   ```
   You want a ✓ next to **Android toolchain**. (Visual Studio ✗ is fine — only needed for
   Windows desktop apps.)

## Part D — Create the emulator (a virtual phone)

10. Android Studio → **More Actions → Virtual Device Manager** → **+ (Create Virtual Device)**.
11. Choose **Pixel 8** (any phone works) → **Next**.
12. Choose a system image with **API 35** and **x86_64** (download it if it shows a ↓ icon) → **Next** → **Finish**.
13. Press **▶** to start it once. A phone appears on screen. You can close Android Studio now; keep the emulator open.

## Part E — Set up VS Code

14. Open VS Code → **Extensions** (Ctrl+Shift+X) → search **Flutter** → install the one by
    **Dart Code** (it also installs Dart).
15. **File → Open Folder…** → choose `C:\Users\jawad\OneDrive\Desktop\Rahmeen Mobile app project`.

## Part F — Run it

16. Start the backend: **Terminal → Run Task… → Start backend**
    (or in a terminal: `cd backend; uv run python -m uvicorn app.main:app --port 8000`).
    Wait for `Application startup complete`.
17. In the bottom-right corner of VS Code click the device name and pick your **emulator**
    (e.g. `sdk gphone64 x86 64`). If it is not running, pick it from the list to start it.
18. Open **Run and Debug** (Ctrl+Shift+D) → choose **Student app (choose device bottom-right)** → press **▶** (or F5).
    The first build takes 5–10 minutes (Gradle downloads its parts). Later runs take under a minute.
19. The EduRecommend app opens on the emulator. It reaches your backend automatically
    (`http://10.0.2.2:8000` = your laptop from inside the emulator).

While it runs: save a Dart file to **hot reload**; the debug toolbar has restart and stop.

Without VS Code, the same from PowerShell:
```powershell
cd mobile; flutter emulators
```
```powershell
flutter emulators --launch <emulator id from the list>
```
```powershell
flutter run
```

---

## If something goes wrong

| Problem | Fix |
|---|---|
| `flutter doctor`: "Unable to locate Android SDK" | Finish Part A step 3. Then `flutter config --android-sdk "%LOCALAPPDATA%\Android\Sdk"` |
| `cmdline-tools component is missing` | Part A step 4 |
| Emulator very slow or says acceleration is not available | Part B, then restart |
| App shows "Could not connect" | Backend not running (step 16), or it was started with a port other than 8000 |
| First build stuck on "Running Gradle task" | Normal the first time; wait. If it fails, check internet and run again |
| Windows blocks a program from running | Smart App Control is already off on this laptop; if your antivirus asks, allow Android Studio / Flutter |

## Real phone instead of emulator (optional)
Turn on **Developer options → USB debugging** on the phone, connect it with a cable, and
choose it in the VS Code device list. The phone cannot use `10.0.2.2`; start the backend with
`--host 0.0.0.0` and run the app with
`--dart-define=API_BASE_URL=http://<your laptop's Wi-Fi IP>:8000` (both on the same Wi-Fi).
