$ErrorActionPreference = "Stop"

# Build both Windows distributions without letting one overwrite the other.
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "Creating project virtual environment..."
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment. Is Python 3.11+ installed?" }
}

Write-Host "Installing/updating build dependencies..."
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Application dependency installation failed." }

& $Python -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed." }

# Remove only prior generated outputs for these two builds.
foreach ($PathToRemove in @(
    ".\release\portable\LiveIsoDriverInjector",
    ".\release\standalone\LiveIsoDriverInjector.exe",
    ".\build\portable",
    ".\build\standalone",
    ".\build\specs\portable",
    ".\build\specs\standalone"
)) {
    if (Test-Path $PathToRemove) {
        Remove-Item -LiteralPath $PathToRemove -Recurse -Force
    }
}

New-Item -ItemType Directory -Force -Path `
    ".\release\portable", ".\release\standalone", `
    ".\build\portable", ".\build\standalone", `
    ".\build\specs\portable", ".\build\specs\standalone" | Out-Null

Write-Host "`nBuilding portable folder version..."
& $Python -m PyInstaller --noconfirm --clean --windowed `
    --name LiveIsoDriverInjector `
    --distpath ".\release\portable" `
    --workpath ".\build\portable" `
    --specpath ".\build\specs\portable" `
    ".\src\main.py"
if ($LASTEXITCODE -ne 0) { throw "Portable build failed. See the error above." }

Write-Host "`nBuilding standalone EXE..."
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name LiveIsoDriverInjector `
    --distpath ".\release\standalone" `
    --workpath ".\build\standalone" `
    --specpath ".\build\specs\standalone" `
    ".\src\main.py"
if ($LASTEXITCODE -ne 0) { throw "Standalone build failed. See the error above." }

Write-Host "`nBuilds completed:"
Write-Host "Portable:   $ProjectRoot\release\portable\LiveIsoDriverInjector\"
Write-Host "Standalone: $ProjectRoot\release\standalone\LiveIsoDriverInjector.exe"
Write-Host "`nKeep the entire portable folder together. Test both builds before distributing."
