
@echo off
chcp 65001 >nul  && echo UTF-8 encoding set

cd /d C:\Users\LENOVO\Desktop\MeSO

@REM :: Log Python version (for debug)
C:\Users\LENOVO\Desktop\MeSO\myenv\Scripts\python.exe --version >> logs\motivation_log.txt 2>&1

@REM :: Run the motivation script
C:\Users\LENOVO\Desktop\MeSO\myenv\Scripts\python.exe daily_motivation.py >> logs\motivation_log.txt 2>&1

@REM Pause to keep window open (debugging only — optional)
pause







