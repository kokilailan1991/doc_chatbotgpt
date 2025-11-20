Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing Python and Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = py --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "Python not found. Installing Python 3.12..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 --override "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" --accept-package-agreements --accept-source-agreements
    Write-Host "Please restart your terminal after Python installation." -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit
}

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check if pip is available
Write-Host ""
Write-Host "Checking pip..." -ForegroundColor Yellow
try {
    $pipVersion = py -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "pip found: $pipVersion" -ForegroundColor Green
    } else {
        throw "pip not found"
    }
} catch {
    Write-Host "pip not found. Installing pip..." -ForegroundColor Yellow
    Write-Host "Downloading get-pip.py..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "get-pip.py"
    Write-Host "Installing pip..." -ForegroundColor Yellow
    py get-pip.py
    Remove-Item get-pip.py -ErrorAction SilentlyContinue
}

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
py -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
py -m pip install -r requirements.txt

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run the app, use: py app.py" -ForegroundColor Cyan
Write-Host "Or run: .\run_app.ps1" -ForegroundColor Cyan
Write-Host ""

