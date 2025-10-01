# NFC Proxy System - PowerShell Test Script

Write-Host "Running NFC Proxy System Tests..." -ForegroundColor Green
Write-Host ""

# Use the virtual environment Python
& "venv\Scripts\python.exe" test_setup.py

Write-Host ""
Read-Host "Press Enter to continue"
