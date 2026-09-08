@echo off
setlocal
call .venv\Scripts\activate.bat
cd Python
python run_all.py
endlocal
