#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "  ===================================================="
echo "         LingCorpus Platform - Inicio Rapido"
echo "  ===================================================="
echo ""

# Verifica Python
if ! command -v python3 &>/dev/null; then
    echo -e "  ${RED}[ERRO]${NC} Python3 nao encontrado. Instale em python.org"
    exit 1
fi

# Cria credenciais Streamlit
mkdir -p "$HOME/.streamlit"
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
    printf '[general]\nemail = ""\n' > "$HOME/.streamlit/credentials.toml"
fi

# Cria venv
if [ ! -d ".venv" ]; then
    echo -e "  ${YELLOW}[1/4]${NC} Criando ambiente virtual..."
    python3 -m venv .venv
else
    echo -e "  ${GREEN}[1/4]${NC} Ambiente virtual encontrado."
fi

# Instala dependencias
echo -e "  ${YELLOW}[2/4]${NC} Verificando dependencias..."
.venv/bin/pip install -q -e . 2>/dev/null || .venv/bin/pip install -e .

# Mata processos anteriores
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:8501 2>/dev/null | xargs kill -9 2>/dev/null || true

# Inicia API
echo -e "  ${YELLOW}[3/4]${NC} Iniciando API REST (porta 8000)..."
.venv/bin/python -m uvicorn lingcorpus.app:app --host 127.0.0.1 --port 8000 &
API_PID=$!

# Aguarda API
echo "         Aguardando API..."
for i in $(seq 1 15); do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "         ${GREEN}API pronta!${NC}"
        break
    fi
    if [ "$i" -eq 15 ]; then
        echo -e "  ${RED}[ERRO]${NC} API nao iniciou."
        kill $API_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Abre navegador
echo -e "  ${GREEN}[4/4]${NC} Abrindo dashboard no navegador..."
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:8501 &
elif command -v open &>/dev/null; then
    open http://localhost:8501 &
fi

# Cleanup ao sair
cleanup() {
    echo ""
    echo "  Encerrando..."
    kill $API_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# Inicia Dashboard
.venv/bin/python -m streamlit run src/lingcorpus/dashboard.py --server.port 8501 --server.headless true

cleanup
