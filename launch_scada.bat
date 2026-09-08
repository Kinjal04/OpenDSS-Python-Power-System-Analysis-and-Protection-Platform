@echo off
setlocal
call .venv\Scripts\activate.bat
cd Python
streamlit run app.py
endlocal
