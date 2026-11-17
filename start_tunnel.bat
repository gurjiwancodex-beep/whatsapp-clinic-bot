@echo off
title WhatsApp Clinic Bot - Cloudflare Public Tunnel
echo ========================================================
echo 🌐 Creating Free Public HTTPS Tunnel for your Bot & Admin...
echo ========================================================
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8000
pause
