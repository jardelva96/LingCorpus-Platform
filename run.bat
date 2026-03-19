@echo off
echo ============================================
echo   LingCorpus Platform - Iniciando...
echo ============================================

:: Cria credenciais Streamlit no home do usuario
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general] > "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "" >> "%USERPROFILE%\.streamlit\credentials.toml"
)

:: Cria venv se nao existir
if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

:: Instala dependencias
echo Instalando dependencias...
.venv\Scripts\pip.exe install -q -e ".[dev]" 2>nul

:: Inicia API em background
echo Iniciando API em background (porta 8000)...
start /B .venv\Scripts\python.exe -m uvicorn lingcorpus.app:app --host 0.0.0.0 --port 8000

:: Aguarda API iniciar
timeout /t 3 /nobreak >nul

:: Inicia Dashboard
echo Abrindo dashboard...
.venv\Scripts\python.exe -m streamlit run src/lingcorpus/dashboard.py --server.port 8501

pause
