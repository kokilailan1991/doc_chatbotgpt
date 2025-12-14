# Test Server Script
Write-Host "Starting Flask app on port 5000..." -ForegroundColor Green

# Set port
$env:PORT = 5000

# Try different Python commands
$pythonCmds = @("py", "python", "python3")

foreach ($cmd in $pythonCmds) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $version -match "Python") {
            Write-Host "Found Python: $cmd" -ForegroundColor Yellow
            Write-Host "Starting server on http://localhost:5000" -ForegroundColor Cyan
            Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
            Write-Host ""
            & $cmd app.py
            break
        }
    } catch {
        continue
    }
}

if (-not $version) {
    Write-Host "ERROR: Python not found in PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please either:" -ForegroundColor Yellow
    Write-Host "1. Add Python to your PATH" -ForegroundColor Yellow
    Write-Host "2. Or run: .\run_app.ps1 (if Python is installed)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

