@echo off
rem AI-Cowork launcher - delegates everything to the Python CLI in 98_tools\
rem Usage: aicowork doctor, aicowork init FOLDER, aicowork viz, aicowork --help
rem With uv: uv picks (or fetches) a Python that 98_tools\pyproject.toml accepts and
rem installs the command line only; "viz" adds the viewer the first time it runs.
rem Without uv: a Python the tools accept runs every command except the viewer;
rem the command line says plainly when yours is too old.
set "AICOWORK_CALLER_DIR=%CD%"
cd /d "%~dp0"
if not exist "98_tools\apps\aicowork" (
  echo   This folder has no tools ^(98_tools^): the kernel works with files alone - see 99_system\README.md
  pause
  exit /b 1
)
where uv >nul 2>nul
if %errorlevel% equ 0 (
  set UV_LINK_MODE=copy
  uv run --locked --project 98_tools --package aicowork --extra seal aicowork %*
) else (
  set "PYTHONPATH=%~dp098_tools\apps\aicowork\src"
  where py >nul 2>nul
  if errorlevel 1 (
    where python >nul 2>nul || echo   Python is needed: https://www.python.org/downloads/ - or uv, which fetches it: https://docs.astral.sh/uv/
    python -m aicowork %*
  ) else (
    py -3 -m aicowork %*
  )
)
if "%~1"=="" pause
