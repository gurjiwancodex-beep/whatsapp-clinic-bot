@echo off
title WhatsApp QR Code Bridge - Singla Eye Care Bot
color 0A

echo ======================================================================
echo           CLINIC WHATSAPP BOT - 1-CLICK QR CONNECT
echo ======================================================================
echo.
echo [1] Setting up Node.js environment...
set "PATH=C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.20.0-win-x64;%PATH%"

cd /d "E:\whatsapp-clinic-bot\whatsapp-qr-bridge"

echo [2] Starting WhatsApp Web Bridge...
echo.
echo **********************************************************************
echo  INSTRUCTIONS:
echo  1. Thalle ik QR Code banega.
echo  2. Apne Phone te WhatsApp open karo.
echo  3. 3-dots (ya Settings) -> "Linked Devices" -> "Link a Device" dabao.
echo  4. Is QR Code nu phone de camera naal scan karo.
echo  5. Bas! Tuhada WhatsApp Bot live chal payega (No GST / No Meta fees)!
echo **********************************************************************
echo.

node index.js

echo.
echo Bridge stopped.
pause
