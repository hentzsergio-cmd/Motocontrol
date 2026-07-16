@echo off
chcp 65001 >nul
title Motocontrol
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════╗
echo  ║              Motocontrol             ║
echo  ╚══════════════════════════════════════╝
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Node.js nao encontrado. Instale em https://nodejs.org
  pause
  exit /b 1
)

if not exist "package.json" (
  echo [ERRO] package.json nao encontrado nesta pasta.
  echo Coloque este .bat na pasta do App Motocontrol ^(onde esta o package.json^).
  pause
  exit /b 1
)

if not exist "node_modules\" (
  echo Instalando dependencias...
  call npm install
  if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
  )
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
  echo Liberando porta 5173 ^(PID %%P^)...
  taskkill /F /PID %%P >nul 2>&1
)

echo Iniciando Motocontrol em http://localhost:5173
echo.
start "" http://localhost:5173
call npm run dev

if errorlevel 1 (
  echo.
  echo [ERRO] Servidor encerrado com erro.
  pause
)
