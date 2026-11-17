@echo off
title WhatsApp AI Bot - 1-Click Connect
color 0F

echo ======================================================================
echo           CLINIC WHATSAPP BOT - REAL WHATSAPP CONNECT
echo ======================================================================
echo.
set "PATH=C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.20.0-win-x64;%PATH%"

cd /d "E:\whatsapp-clinic-bot\whatsapp-qr-bridge"

node index.js

echo.
echo Process ended.
pause
