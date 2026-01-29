@echo off
set "BASE_DIR=%~dp0"
set "PYTHON_EXE=%BASE_DIR%portable_env\python.exe"

echo [Portable Mode] Using embedded Python...

REM Run main program
"%PYTHON_EXE%" "%BASE_DIR%mcp_server.py" %*

pause
