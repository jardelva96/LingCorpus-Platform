#!/bin/bash
echo "============================================"
echo "  LingCorpus Platform - Iniciando..."
echo "============================================"

# Cria credenciais Streamlit
mkdir -p "$HOME/.streamlit"
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
    echo '[general]' > "$HOME/.streamlit/credentials.toml"
    echo 'email = ""' >> "$HOME/.streamlit/credentials.toml"
fi

# Cria venv se nao existir
if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv .venv
fi

# Instala dependencias
echo "Instalando dependencias..."
.venv/bin/pip install -q -e ".[dev]" 2>/dev/null

# Inicia API em background
echo "Iniciando API em background (porta 8000)..."
.venv/bin/python -m uvicorn lingcorpus.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Aguarda API iniciar
sleep 3

# Inicia Dashboard
echo "Abrindo dashboard..."
.venv/bin/python -m streamlit run src/lingcorpus/dashboard.py --server.port 8501

# Finaliza API ao sair
kill $API_PID 2>/dev/null
