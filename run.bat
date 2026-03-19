@echo off
setlocal
title LingCorpus Platform
color 0A

echo.
echo  ====================================================
echo          LingCorpus Platform - Inicio Rapido
echo  ====================================================
echo.

:: Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado. Instale em python.org
    pause
    exit /b 1
)

:: Cria credenciais Streamlit para pular prompt de email
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general] > "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "" >> "%USERPROFILE%\.streamlit\credentials.toml"
)

:: Cria venv se nao existir
if not exist ".venv" (
    echo  [1/4] Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
) else (
    echo  [1/4] Ambiente virtual encontrado.
)

:: Instala dependencias
echo  [2/4] Verificando dependencias...
.venv\Scripts\pip.exe install -q -e . 2>nul
if errorlevel 1 (
    echo         Instalando dependencias pela primeira vez...
    .venv\Scripts\pip.exe install -e .
)

:: Mata processos anteriores nas portas 8000 e 8501
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Inicia API em background
echo  [3/4] Iniciando API REST (porta 8000)...
start /B "" .venv\Scripts\python.exe -m uvicorn lingcorpus.app:app --host 127.0.0.1 --port 8000 >nul 2>&1

:: Aguarda API ficar pronta
echo         Aguardando API...
set /a attempts=0
:wait_api
set /a attempts+=1
if %attempts% gtr 15 (
    echo  [ERRO] API nao iniciou. Verifique se a porta 8000 esta livre.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
.venv\Scripts\python.exe -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" >nul 2>&1
if errorlevel 1 goto wait_api
echo         API pronta!

:: Abre navegador automaticamente
echo  [4/4] Abrindo dashboard no navegador...
start http://localhost:8501

:: Inicia Dashboard (bloqueia aqui)
.venv\Scripts\python.exe -m streamlit run src/lingcorpus/dashboard.py --server.port 8501 --server.headless true

:: Cleanup ao fechar
echo.
echo  Encerrando...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
endlocal
