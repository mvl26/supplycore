@echo off
REM SupplyCore one-click installer for Windows — double-click this file.
REM It just runs install.ps1 with an execution-policy bypass.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
pause
