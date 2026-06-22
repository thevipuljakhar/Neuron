@echo off
echo.
echo  NEURON — one-time environment setup
echo.
pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo.
  echo  pip install FAILED — fix the error above and re-run setup.bat
  pause
  exit /b 1
)
echo.
echo  Installing Playwright Chromium (needed for PM-KUSUM / Surya Ghar scrape fallback)...
playwright install chromium
echo.
echo  Setup complete. Use start.bat to launch NEURON.
pause
