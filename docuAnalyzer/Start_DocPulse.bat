@echo off
chcp 65001 >nul
title DocPulse Launcher
echo ⚡ Starting DocPulse Local Environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    pause
    exit
)
if not exist "venv" (
    echo [SETUP] Creating isolated environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install streamlit pypdf2 pandas matplotlib
) else (
    call venv\Scripts\activate.bat
)
echo 🚀 Launching DocPulse...
streamlit run doc_analyzer.py