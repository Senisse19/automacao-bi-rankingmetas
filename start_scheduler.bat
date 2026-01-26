@echo off
cd /d "%~dp0"

echo ----------------------------------------------------
echo [START] Iniciando Scheduler de Automacao (Studio)...
echo ----------------------------------------------------

:: Verificar se .venv existe
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Ativando ambiente virtual (.venv)...
    call .venv\Scripts\activate.bat
) else (
    echo [AVISO] Ambiente virtual nao encontrado! Tentando python global...
)

echo [INFO] Executando scheduler.py...
echo.

python scheduler.py

echo.
echo [END] O scheduler foi encerrado.
pause
