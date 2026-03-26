@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

if exist "secrets.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("secrets.env") do (
        set "KEY=%%A"
        set "VAL=%%B"
        if defined KEY (
            if not "!KEY:~0,1!"=="#" (
                set "!KEY!=!VAL!"
            )
        )
    )
)

"%PYTHON_EXE%" "cat_detector.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

popd >nul
exit /b %EXIT_CODE%
