# Installation Instructions

## Step 1: Install Python

If Python is not properly installed with pip, please install it:

### Option A: Using Winget (Recommended)
```powershell
winget install Python.Python.3.12
```

### Option B: Download from Python.org
1. Go to https://www.python.org/downloads/
2. Download Python 3.12 or later
3. **IMPORTANT**: During installation, check "Add Python to PATH" and "Install pip"

## Step 2: Verify Installation

Open a new PowerShell terminal and run:
```powershell
python --version
pip --version
```

If both commands work, proceed to Step 3.

## Step 3: Install Dependencies

Run the installation script:
```powershell
.\install_dependencies.ps1
```

Or manually install:
```powershell
pip install -r requirements.txt
```

## Step 4: Run the Application

```powershell
python app.py
```

Or use the run script:
```powershell
.\run_app.ps1
```

The app will be available at: http://localhost:8080

## Troubleshooting

If you get "No module named pip" error:
1. Download get-pip.py: https://bootstrap.pypa.io/get-pip.py
2. Run: `python get-pip.py`
3. Then install dependencies: `pip install -r requirements.txt`

