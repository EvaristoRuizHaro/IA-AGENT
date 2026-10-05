@echo off
REM Lanza el agente usando el Python del entorno virtual y guarda lo que pase en registro.log
cd /d "%~dp0"
set PYTHONUTF8=1
echo ===== %date% %time% ===== >> registro.log
venv\Scripts\python.exe agente.py >> registro.log 2>&1
