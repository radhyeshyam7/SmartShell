# SmartShell 2.0 - Start Backend Server
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -ErrorAction SilentlyContinue

$WorkspaceRoot = Get-Location
$VenvPython = "$WorkspaceRoot\venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Virtual environment not found. Running setup..." -ForegroundColor Yellow
    .\scripts\setup_windows.ps1
}

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "       Starting SmartShell 2.0 Backend Server       " -ForegroundColor Cyan
Write-Host "       http://127.0.0.1:8000 (API & WebSockets)     " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

& $VenvPython -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
