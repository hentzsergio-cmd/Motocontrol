@echo off
chcp 65001 >nul
title Atualizar Motocontrol
cd /d "%~dp0"

where git >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Git nao encontrado. Instale o Git em https://git-scm.com/download/win
  pause
  exit /b 1
)

if not exist ".git\" (
  echo [ERRO] Esta pasta ainda nao esta conectada ao GitHub.
  echo Rode o comando de conexao que o Devin te passou ^(uma unica vez^).
  pause
  exit /b 1
)

echo Baixando atualizacoes do GitHub...
git pull origin main
if errorlevel 1 (
  echo.
  echo [ERRO] Nao foi possivel atualizar. Verifique sua conexao/login do GitHub.
  pause
  exit /b 1
)

echo.
echo Pronto! Motocontrol atualizado.
pause
