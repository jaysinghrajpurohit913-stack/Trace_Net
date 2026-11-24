@echo off
rem Double-click this file to start TraceNet (Windows).
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed. Install Python 3.10 or newer from python.org, tick "Add to PATH", then run this again.
  pause & exit /b 1
)
if not exist ".venv" (
  echo First time setup, this takes a few minutes...
  python -m venv .venv
  call ".venv\Scripts\activate.bat"
  python -m pip install -q --upgrade pip
  pip install -q -r requirements.txt
) else (
  call ".venv\Scripts\activate.bat"
)
echo Opening TraceNet in your browser. Close this window to stop it.
streamlit run app.py
pause
