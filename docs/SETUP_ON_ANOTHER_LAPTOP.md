# Set up EduRecommend on another Windows laptop

Time: about 30–45 minutes (mostly downloads). Needs: Windows 10/11, 8 GB RAM or more,
about 10 GB free disk space, internet.

## 1. Copy the project
Either:
- **Zip (simplest):** copy `EduRecommend-project.zip` (USB, Google Drive, WhatsApp document, etc.),
  then right-click → **Extract All…** to e.g. `C:\Users\<name>\Documents\EduRecommend`.
  Avoid a OneDrive folder if possible (syncing slows builds).
- **Git (if the project is on GitHub):**
  `git clone <repository link> C:\Users\<name>\Documents\EduRecommend`

The zip does **not** contain `backend\.env` (passwords) or the local database. Each laptop
makes its own.

## 2. One command installs everything (recommended)
Open the extracted folder in File Explorer, click the address bar, type `powershell`, press
Enter, and run:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-everything.ps1
```
It shows what is missing, asks you to type **Y**, then installs Git, Google Chrome, uv
(Python) and Flutter (about 2–3 GB, 20–40 minutes), and finally runs the project setup.
It warns if Windows Smart App Control is on (see the table below). If it stops with an error,
close the window, open a new one, and run the same command again — it skips what is done.

Then go to step 4. (Steps 2b and 3 are the manual way, only needed if the script fails.)

## 2b. Install the tools by hand (only if the script fails)
1. **Google Chrome** — https://www.google.com/chrome/
2. **Git for Windows** — https://git-scm.com/download/win (defaults are fine; Flutter needs it)
3. **uv** (installs Python for you) — open PowerShell and run:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
4. **Flutter SDK** — follow https://docs.flutter.dev/get-started/install/windows
   (Windows → Web is enough). The simple way, in PowerShell:
   ```powershell
   git clone https://github.com/flutter/flutter.git -b stable $env:USERPROFILE\flutter
   ```
   Then add `C:\Users\<name>\flutter\bin` to the user **Path**: Start → "Edit environment
   variables for your account" → **Path** → **Edit** → **New** → paste → **OK**.
5. **Close PowerShell and open a new one.** Check:
   ```powershell
   flutter --version
   ```
   (The first run downloads more Flutter parts; that is normal.)

## 3. Run the setup script (one time)
Open PowerShell **in the project folder** (in File Explorer: open the folder, type
`powershell` in the address bar, press Enter) and run:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```
It checks the tools, installs all packages, creates `backend\.env` with a new random staff
password, and runs the backend tests. Every line should say **OK**.

## 4. Start the app (every time)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```
Three windows open (backend, student app, admin panel) and Chrome opens twice:
- Student app: http://localhost:5173 — create an account and try **Find my universities**.
- Admin panel: http://localhost:5174 — sign in as `admin@example.com` or
  `verifier@example.com`; the password is the line in `backend\.env`.
- API docs: http://localhost:8000/docs

To stop: close the three windows.

## Problems and fixes

| Problem | Fix |
|---|---|
| "running scripts is disabled on this system" | Use the full command above (with `-ExecutionPolicy Bypass`) |
| `flutter` / `uv` "not recognized" | Open a **new** PowerShell window; check the Path step (2.4) |
| "An Application Control policy has blocked this file" | Windows **Smart App Control** is blocking Flutter. Windows Security → App & browser control → Smart App Control → **Off** (it cannot be turned back on without resetting Windows — the laptop owner must decide) |
| `uv sync` fails with a certificate error | The script retries with `--system-certs` automatically; if it still fails, check the internet connection |
| Backend window shows "address already in use" | Something else uses port 8000; close it or restart the laptop |
| App says "Could not connect" | The backend window was closed or shows an error |
| Want to start again with fresh demo data | Close the windows, delete `backend\dev.db`, start again |

## Optional
- **VS Code:** install the **Flutter** extension (by Dart Code) and open the project folder;
  the Run and Debug panel has "Student app" and "Admin panel", and Terminal → Run Task has
  "Start backend".
- **Android emulator:** see [ANDROID_EMULATOR_SETUP.md](ANDROID_EMULATOR_SETUP.md).
