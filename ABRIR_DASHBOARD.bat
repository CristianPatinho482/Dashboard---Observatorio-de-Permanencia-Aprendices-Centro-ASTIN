@echo off
setlocal
set "HTML=%~dp0dashboard\index.html"
if not exist "%HTML%" (
  echo No se encontro dashboard\index.html
  echo Ejecute primero: python -X utf8 scripts\06_generar_dashboard.py
  pause
  exit /b 1
)
start "" "%HTML%"
exit /b 0
