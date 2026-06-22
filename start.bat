@echo off
setlocal
title NEURON — Indian RE Intelligence Terminal

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║   NEURON  —  Indian RE Intelligence Terminal                 ║
echo  ║   by Vipul Jakhar                                            ║
echo  ╠══════════════════════════════════════════════════════════════╣
echo  ║  PHASES ACTIVE                                               ║
echo  ║   P14  Living Memory   — beliefs / IRENA / entity ledger     ║
echo  ║   P15  Nervous System  — pipeline / observatory / weather    ║
echo  ║   P16  God-Tier Memory — MemoryOS, fastembed ONNX, MCP       ║
echo  ║   P17  Executive Fn    — conviction-scored decisions         ║
echo  ║   P18  Data Fixes      — Surya Ghar, KUSUM, PDF export       ║
echo  ║   P19  Cockpit UI      — 6-surface IA, 3D parallax BG        ║
echo  ║   P19.5 Deep-Read      — Board Secretary one-pager agent     ║
echo  ║   P20  Reach & Voice   — IMF macro, Polymarket, Telegram     ║
echo  ║   P21  Visualisations  — ECharts 5, rainbow, anti-gravity    ║
echo  ║   P22  API Audit       — 54 endpoints wired in UI            ║
echo  ║   P23  Media BG        — video BG dark/light, drag panels    ║
echo  ╠══════════════════════════════════════════════════════════════╣
echo  ║   URL  →  http://localhost:5000                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

rem Auto-open browser after a 3-second head-start for Flask to bind
start "" cmd /c "timeout /t 3 >nul && start http://localhost:5000"

rem Launch server (dependencies installed once via setup.bat — offline-safe)
python "%~dp0neuron.py"

echo.
echo  NEURON stopped.
pause
endlocal
