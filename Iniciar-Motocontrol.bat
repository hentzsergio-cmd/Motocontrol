@echo off
chcp 65001 >nul
title Motocontrol
cd /d "%~dp0"

if not exist "main.py" (
  echo [ERRO] main.py nao encontrado nesta pasta.
  echo Coloque este .bat na pasta do App Motocontrol ^(onde esta o main.py^).
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale em https://www.python.org/downloads/
    pause
    exit /b 1
  )
)

if exist "requirements.txt" (
  echo Instalando/atualizando dependencias...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo Iniciando Motocontrol...
echo.
".venv\Scripts\python.exe" main.py

if errorlevel 1 (
  echo.
  echo [ERRO] O aplicativo encerrou com erro.
)
pause
