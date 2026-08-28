@echo off
title Loan Eligibility Analyzer - Account Creator
cd /d "%~dp0backend"

python create_user.py %*

echo.
pause
