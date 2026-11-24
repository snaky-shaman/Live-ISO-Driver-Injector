# Live ISO Driver Injector

**Version:** 0.1.0 (Phase 1 prototype)  
**Platform:** Windows 10/11, 64-bit  
**Purpose:** Organize and audit Linux driver files before any future image-injection workflow.

## Important: what this version does—and does not do

This is a preservation-first **staging prototype**. It can:

- Select a Linux ISO or disk-image file as a project reference.
- Import multiple driver/package files.
- Calculate and display each imported file's SHA-256 hash.
- Store per-driver manual-update and network-update retention preferences.
- Store a source type, source location, and update-strategy preference as project metadata.
- Detect duplicate imported filenames and compare their hashes.
- Save a JSON project manifest and separate staging copies of the imported drivers.

**It does not modify, rebuild, mount, or flash an ISO, IMG, USB drive, or Tails installation.** It does not install drivers, resolve Linux package dependencies, download drivers, use Tor, patch Tails, or verify that a driver is compatible. The source image is only recorded as a project reference. Do not treat a successful project save or conflict scan as proof that a driver will work.

The app intentionally does not overwrite or delete the original driver files. A duplicate filename is a warning to inspect; it is not an instruction to replace anything.

## Project layout

```text
Live ISO Driver Injector/
├── README.md
├── requirements.txt
├── build_windows.ps1
└── src/
    └── main.py
```

## Build on Windows from a clean checkout

You need:

- Windows 10 or 11, 64-bit.
- Python 3.11 or newer from https://www.python.org/downloads/windows/
- PowerShell.
- An internet connection for the first dependency installation.

During Python setup, enable **Add python.exe to PATH** (or use the Python Launcher `py`).

1. Extract the project ZIP to a normal folder, for example `C:\Live ISO Driver Injector`.
2. Open that folder in File Explorer.
3. In the address bar, type `powershell` and press Enter. The PowerShell prompt should show the project folder.
4. Run the build script:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\build_windows.ps1
   ```

   The execution-policy command applies only to that PowerShell window. If your organization's device policy blocks scripts, use the manual commands below instead.

The script creates a local virtual environment, installs the app dependencies and PyInstaller, and builds **both** Windows distribution formats into separate folders. It does not delete your source files.

### Manual build commands

If you prefer to enter the steps yourself, run these commands from the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pyinstaller
```

Build the portable folder version:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name LiveIsoDriverInjector --distpath .\release\portable --workpath .\build\portable --specpath .\build\specs\portable .\src\main.py
```

Build the single-file version separately:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name LiveIsoDriverInjector --distpath .\release\standalone --workpath .\build\standalone --specpath .\build\specs\standalone .\src\main.py
```

Using separate output and work folders prevents one build from replacing the other.

## Where the finished builds are

After a successful build:

**Portable folder build**

```text
release/
└── portable/
    └── LiveIsoDriverInjector/
        ├── LiveIsoDriverInjector.exe
        └── _internal/
            └── ... bundled runtime files ...
```

To distribute this version, ZIP the **entire** `LiveIsoDriverInjector` folder. Keep `_internal` beside the EXE; the EXE needs it.

**Single-file build**

```text
release/
└── standalone/
    └── LiveIsoDriverInjector.exe
```

To distribute this version, provide the EXE. PyInstaller bundles the Python runtime and detected application dependencies inside it and extracts what it needs when launched. It is not an installer.

Both builds are Windows builds and should be tested on another compatible Windows computer before sharing. A computer does not normally need Python or a separate PySide6 installation to run either build. Windows security software may warn about unsigned, newly built executables.

## What belongs in the compiled distribution?

For the current app, distribute only one of these:

- **Portable:** the complete `release\portable\LiveIsoDriverInjector` folder.
- **Single-file:** `release\standalone\LiveIsoDriverInjector.exe`.

Do **not** include the development environment, source code, or build cache in the end-user package. The next section explains each project item.

## Files and folders: keep for development vs. distribute

| Item | Keep in your development project? | Include in end-user compiled release? |
|---|---:|---:|
| `src\main.py` | Yes | No |
| `requirements.txt` | Yes | No |
| `README.md` | Yes | Optional; useful documentation |
| `build_windows.ps1` | Yes | No |
| `.venv\` | Optional; local Python environment | No |
| `build\` | No; generated build cache, safe to recreate | No |
| `dist\` | No; older/default PyInstaller output, if present | No |
| `release\` | Generated final outputs | Include only the selected release output described above |
| `__pycache__\` and `*.pyc` | No; generated Python cache | No |
| `*.spec` | Generated PyInstaller recipe; keep only if you customize/reuse it | No, not needed by end users |
| `*.json` project manifest | Keep if it is a project you want to reopen/reference | Not part of the app; share separately only when intended |
| `*_staging\` folders | Keep if you want the staged driver copies | Not part of the app; share separately only when intended |

Do not delete `src`, `requirements.txt`, or the build script from your **development copy** just because they are not included in the compiled release. They are needed to maintain and rebuild the app.

## Running the app from source (without compiling)

From the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\src\main.py
```

## First test

1. Launch the app.
2. Click **Choose image…** and select a Linux ISO or disk image. This only records its path.
3. Click **Add driver files…** and select one or more driver files.
4. Select each driver and set its preferences.
5. Click **Apply settings to selected driver** before switching to another driver.
6. Click **Analyze conflicts** to review duplicate filenames and hashes.
7. Click **Save project…** to write a JSON manifest and copy the selected drivers into a staging folder.

Use copies of files for testing. This prototype does not need access to a USB drive.

## Known limitations

- Drivers are imported as individual files; folder import is not implemented.
- Conflict scanning checks duplicate names among the imported files only. It does not inspect the selected ISO for existing files.
- Same-name files with identical hashes are reported as duplicate content; same-name files with different hashes are reported as conflicts.
- Source and update-strategy fields are saved as metadata only. No downloads occur.
- Manual/network update retention settings are saved as metadata only. No update process is modified.
- No Tor, onion-service, Git, or torrent connection is implemented.
- No Linux package dependency, kernel ABI, architecture, module-signing, firmware, or initramfs compatibility checks are implemented.
- Tails-specific image formats, boot handling, updater behavior, and security implications are not implemented.

## Planned development direction

1. Read-only image inspection and distribution/version detection.
2. A controlled Linux build worker for explicitly supported image formats and distributions.
3. Driver/package dependency and kernel compatibility checks.
4. Safe injection into supported image files, with backups, verification, and logs.
5. Separate Tails-specific investigation and compatibility testing.
6. Optional advanced conflict handling with explicit confirmation, backups, diffs, and rollback.
7. Carefully designed network retrieval, including Tor-aware behavior where supported.

Tails is designed around authenticity and integrity protections. A modified image may fail official integrity checks and may no longer provide the assurances of an unmodified official release. Do not use a modified image for sensitive activity unless you understand and accept those consequences.

## Troubleshooting

- **`py` is not recognized:** reinstall Python and enable the Python Launcher and PATH options, or use the full path to `python.exe`.
- **The app starts from source but not as an EXE:** rebuild from the project root, then test the portable folder build. If it still fails, launch the EXE from PowerShell to capture any error output.
- **The portable EXE was moved by itself:** restore the complete folder, including `_internal`.
- **Windows blocks the script:** use the manual build commands, or ask the device administrator if the computer is managed.
- **A build fails:** copy the complete error text from PowerShell. Do not delete your source folder; `build` and `release` outputs can be regenerated.
