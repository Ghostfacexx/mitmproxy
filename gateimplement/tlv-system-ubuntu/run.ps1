# NFC Proxy System - PowerShell Run Script

Write-Host "Starting NFC Proxy System..." -ForegroundColor Green
Write-Host ""

# Use the virtual environment Python
& "venv\Scripts\python.exe" main.py

Write-Host ""
Write-Host "NFC Proxy System stopped." -ForegroundColor Yellow
Read-Host "Press Enter to continue"
