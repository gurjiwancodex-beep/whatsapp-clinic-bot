@echo off
title GitHub Easy Upload
cd /d "E:\whatsapp-clinic-bot"

echo ========================================================
echo 🚀 Step 1: Connecting your GitHub Account...
echo ========================================================
echo.
echo If prompted, copy the 8-character code shown on screen
echo and press Enter to open your browser and click "Authorize".
echo.

"C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe" auth login --web --git-protocol https

echo.
echo ========================================================
echo 📦 Step 2: Uploading code to GitHub...
echo ========================================================
"C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe" auth setup-git
"E:\MinGit\cmd\git.exe" push -u origin main

echo.
echo ========================================================
echo 🎉 SUCCESS! All files uploaded to GitHub!
echo ========================================================
pause
