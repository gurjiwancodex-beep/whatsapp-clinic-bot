@echo off
title WhatsApp Clinic Bot - Server
cd /d "E:\whatsapp-clinic-bot"
echo ========================================================
echo 🏥 WhatsApp Clinic Bot Server Started!
echo.
echo 💻 PC Browser Link:     http://localhost:8000/admin
echo 📱 Mobile Wi-Fi Link:   http://192.168.31.22:8000/admin
echo 📋 Appointments Link:  http://localhost:8000/appointments
echo ========================================================
echo.
".\.venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
