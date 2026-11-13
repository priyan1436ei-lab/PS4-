@echo off
title AetherPS4 - Modern PlayStation 4 Emulator Core (PRIYAN-A-1)
color 0B
echo Starting AetherPS4 Core...
echo ======================================================================
echo        AETHER PS4 - MODERN PLAYSTATION 4 EMULATOR CORE
echo           Lead Architect & Developer: PRIYAN-A-1
echo ======================================================================
echo.

if exist "AetherPS4_GUI.exe" (
    echo Launching AetherPS4 Desktop GUI...
    start "" "AetherPS4_GUI.exe"
) else if exist "AetherPS4.exe" (
    start "" "AetherPS4.exe"
) else (
    python main.py
)

pause

