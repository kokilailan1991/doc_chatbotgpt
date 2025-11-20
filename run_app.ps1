Write-Host "Starting Flask application on port 8080..." -ForegroundColor Green
Write-Host ""

# Try different Python commands
$pythonCmds = @("py", "python", "python3")

foreach ($cmd in $pythonCmds) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $version -match "Python") {
            Write-Host "Found Python: $cmd" -ForegroundColor Yellow
            Write-Host "Running app.py..." -ForegroundColor Yellow
            Write-Host ""
            & $cmd app.py
            break
        }
    } catch {
        continue
    }
}

if (-not $version) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

