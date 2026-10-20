@echo off
setlocal
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0tiiny.py" %*
) else (
    python "%~dp0tiiny.py" %*
)
exit /b %errorlevel%
