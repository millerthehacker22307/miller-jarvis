@echo off
REM Miller's Jarvis - one-time setup for Windows
cd /d "%~dp0"

echo == Step 1/3: Python check ==
python --version || (echo Python 3 install karo pehle - python.org se, "Add to PATH" tick karke & pause & exit /b 1)

echo == Step 2/3: Ollama ==
where ollama >nul 2>&1 || (echo Ollama nahi mila. https://ollama.com/download se install karke ye file dobara chalao. & pause & exit /b 1)

echo == Step 3/3: Model download (qwen3.5:4b, ~2.6 GB, one time) ==
ollama pull qwen3.5:4b

echo.
echo Setup done! Jarvis chalane ke liye:
echo   python jarvis.py
pause
