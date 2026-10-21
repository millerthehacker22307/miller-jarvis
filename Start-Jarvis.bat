@echo off
REM ============================================================
REM  Miller's Jarvis - one-click launcher (Windows)
REM  Bas double-click karo. Koi command nahi type karna.
REM  Pehli baar thoda setup hoga (Python/Ollama/model), phir
REM  seedha app khul jayega.
REM ============================================================
cd /d "%~dp0"
title Miller's Jarvis

REM ---------- 1) Python dhundo ----------
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY ( where python >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo Python nahi mila. Download page khol raha hun...
  echo Install karte time "Add python.exe to PATH" wala box ZAROOR tick karna,
  echo phir is file ko dobara double-click karna.
  start https://www.python.org/downloads/
  pause
  exit /b 1
)

REM ---------- 2) Ollama dhundo / install ----------
where ollama >nul 2>&1
if errorlevel 1 (
  echo Ollama nahi mila - install kar raha hun ^(winget se^)...
  winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
)
where ollama >nul 2>&1
if errorlevel 1 (
  echo Ollama ab bhi nahi mila. Page khol raha hun - install karke dobara chalao.
  start https://ollama.com/download
  pause
  exit /b 1
)

REM ---------- 3) Ollama start (agar band hai) ----------
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo Ollama start ho raha hai...
  start /min "Ollama" ollama serve
  timeout /t 5 /nobreak >nul
)

REM ---------- 4) Model hai ya nahi ----------
ollama list | findstr /c:"qwen3.5:4b" >nul 2>&1
if errorlevel 1 (
  echo Pehli baar model download hoga ^(~2.6 GB, internet chahiye, thoda time lagega^)...
  ollama pull qwen3.5:4b
)

REM ---------- 5) App kholo ----------
echo Jarvis khul raha hai...
start "" %PY% app.py
exit /b 0
