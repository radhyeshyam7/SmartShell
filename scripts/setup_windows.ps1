# SmartShell 2.0 - Automated Windows Setup Script
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -ErrorAction SilentlyContinue

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "       SmartShell 2.0 Environment Setup             " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$WorkspaceRoot = Get-Location

# 1. Check Python installation
Write-Host "`n[1/4] Checking Python environment..." -ForegroundColor Yellow
if (-not (Test-Path "$WorkspaceRoot\venv")) {
    Write-Host "Creating Python virtual environment in .\venv ..." -ForegroundColor Gray
    python -m venv "$WorkspaceRoot\venv"
}

$VenvPython = "$WorkspaceRoot\venv\Scripts\python.exe"
$VenvPip = "$WorkspaceRoot\venv\Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Error: Virtual environment creation failed." -ForegroundColor Red
    exit 1
}

Write-Host "Installing/Upgrading Python backend dependencies..." -ForegroundColor Gray
& $VenvPip install --upgrade pip --quiet
& $VenvPip install -r "$WorkspaceRoot\backend\requirements.txt" --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] Backend dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Host "[!] Error installing backend dependencies." -ForegroundColor Red
    exit 1
}

# 2. Check Node.js and npm
Write-Host "`n[2/4] Checking Node.js and npm..." -ForegroundColor Yellow
try {
    $nodeVersion = node -v
    $npmVersion = npm -v
    Write-Host "Detected Node.js: $nodeVersion | npm: $npmVersion" -ForegroundColor Gray
} catch {
    Write-Host "[!] Node.js or npm not found in PATH. Please install Node.js (v18+) to run the Web Dashboard." -ForegroundColor Red
}

# 3. Frontend npm setup
Write-Host "`n[3/4] Installing Frontend Dependencies..." -ForegroundColor Yellow
if (Test-Path "$WorkspaceRoot\frontend\package.json") {
    Push-Location "$WorkspaceRoot\frontend"
    npm install
    Pop-Location
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Frontend dependencies installed successfully." -ForegroundColor Green
    } else {
        Write-Host "[!] Error installing frontend dependencies." -ForegroundColor Red
    }
}

# 4. Environment Check
Write-Host "`n[4/4] Environment Configuration Check..." -ForegroundColor Yellow
if (-not (Test-Path "$WorkspaceRoot\.env")) {
    if (Test-Path "$WorkspaceRoot\.env.example") {
        Copy-Item "$WorkspaceRoot\.env.example" "$WorkspaceRoot\.env"
        Write-Host "[!] Created .env from .env.example. Please add your GEMINI_API_KEY to .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "[✓] .env file detected." -ForegroundColor Green
}

Write-Host "`n====================================================" -ForegroundColor Cyan
Write-Host "       Setup Completed Successfully!                " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "To start SmartShell 2.0:" -ForegroundColor White
Write-Host "  1. Run Backend:  .\scripts\start_backend.ps1" -ForegroundColor Gray
Write-Host "  2. Run Frontend: .\scripts\start_frontend.ps1" -ForegroundColor Gray
Write-Host "  3. Access Web UI at: http://localhost:5173" -ForegroundColor Gray
Write-Host "  4. CLI Terminal: .\venv\Scripts\python.exe main.py" -ForegroundColor Gray
