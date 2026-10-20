# SmartShell 2.0 - Start Frontend Dev Server
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -ErrorAction SilentlyContinue

$WorkspaceRoot = Get-Location

if (-not (Test-Path "$WorkspaceRoot\frontend\node_modules")) {
    Write-Host "[!] Frontend dependencies missing. Installing..." -ForegroundColor Yellow
    Push-Location "$WorkspaceRoot\frontend"
    npm install
    Pop-Location
}

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "       Starting SmartShell 2.0 Web Dashboard        " -ForegroundColor Cyan
Write-Host "       http://localhost:5173                        " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

Push-Location "$WorkspaceRoot\frontend"
npm run dev
Pop-Location
