# LingCorpus Platform

**Plataforma web para gerenciamento, validação e análise de corpus textual de pesquisa**

[![CI](https://github.com/jardelva96/LingCorpus-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/jardelva96/LingCorpus-Platform/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Sobre

Sistema completo para gerenciamento de corpus textual voltado a projetos de pesquisa em **Linguística Computacional**, **Linguística de Corpus** e **Processamento de Língua Natural (PLN)**.

### Funcionalidades

| Módulo | Descrição |
|---|---|
| **Autenticação JWT** | Login seguro com controle de acesso baseado em papéis (Admin, Pesquisador, Visitante) |
| **Gerenciamento de Corpus** | Criação de coleções, upload de documentos TXT/CSV, detecção automática de codificação |
| **Validação de Dados** | Verificação de integridade: codificação, caracteres de controle, linhas em branco, consistência |
| **Análise NLP** | Tokenização, frequência de palavras, concordância KWIC, n-gramas, estatísticas descritivas |
| **Controle de Acesso** | Três níveis de permissão com gerenciamento de usuários |
| **Auditoria** | Log completo de todas as ações na plataforma |
| **Exportação** | Exportação de metadados e resultados em CSV |
| **Dashboard** | Interface visual com Streamlit para todas as operações |
| **API REST** | Documentação automática via Swagger (FastAPI) |

---

## Arquitetura

```
┌──────────────────────────────────────────────────┐
│                  Dashboard (Streamlit)            │
│         Gerenciamento · Validação · Análise       │
└──────────────────┬───────────────────────────────┘
                   │ HTTP
┌──────────────────▼───────────────────────────────┐
│                  API REST (FastAPI)               │
│     /api/auth · /api/corpus · /api/analysis       │
├───────────────────────────────────────────────────┤
│  Autenticação   │  Corpus     │  NLP Service      │
│  JWT + bcrypt   │  Service    │  NLTK + regex     │
├───────────────────────────────────────────────────┤
│           SQLAlchemy ORM + SQLite/PostgreSQL       │
│    Users · Corpora · Documents · AuditLogs        │
└───────────────────────────────────────────────────┘
```

---

## Início Rápido

### Requisitos
- Python 3.10 ou superior

### Windows

```powershell
git clone https://github.com/jardelva96/LingCorpus-Platform.git
cd LingCorpus-Platform
.\run.bat
```

### Linux / macOS

```bash
git clone https://github.com/jardelva96/LingCorpus-Platform.git
cd LingCorpus-Platform
chmod +x run.sh
./run.sh
```

O script irá:
1. Criar um ambiente virtual (`.venv`)
2. Instalar todas as dependências
3. Iniciar a API REST na porta **8000**
4. Abrir o dashboard Streamlit na porta **8501**

### Credenciais padrão
| Usuário | Senha |
|---|---|
| `admin` | `admin123` |

### Documentação da API
Acesse `http://localhost:8000/docs` para a documentação Swagger interativa.

---

## Execução Manual

```bash
# Criar venv e instalar
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

# Iniciar API
.venv\Scripts\python -m uvicorn lingcorpus.app:app --reload

# Em outro terminal, iniciar dashboard
.venv\Scripts\python -m streamlit run src/lingcorpus/dashboard.py
```

---

## Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ -v --tb=short

# Lint
ruff check src/ tests/
```

---

## Estrutura do Projeto

```
LingCorpus-Platform/
├── src/lingcorpus/
│   ├── app.py              # Aplicação FastAPI principal
│   ├── auth.py             # Autenticação JWT e RBAC
│   ├── config.py           # Configurações centrais
│   ├── database.py         # Conexão SQLAlchemy
│   ├── models.py           # Modelos de banco de dados
│   ├── schemas.py          # Schemas Pydantic
│   ├── dashboard.py        # Dashboard Streamlit
│   ├── api/
│   │   ├── users.py        # Rotas de autenticação e usuários
│   │   ├── corpus.py       # Rotas de gerenciamento de corpus
│   │   └── analysis.py     # Rotas de análise NLP
│   └── services/
│       ├── nlp_service.py       # Tokenização, frequência, KWIC
│       ├── corpus_service.py    # Lógica de corpus e documentos
│       ├── validation_service.py # Validação de dados textuais
│       └── audit_service.py     # Log de auditoria
├── tests/
│   ├── test_auth.py        # Testes de autenticação (8 testes)
│   ├── test_corpus.py      # Testes de corpus (7 testes)
│   ├── test_nlp.py         # Testes de NLP (10 testes)
│   └── test_validation.py  # Testes de validação (9 testes)
├── .github/workflows/ci.yml
├── pyproject.toml
├── run.bat / run.sh
└── README.md
```

---

## Stack Tecnológica

| Tecnologia | Uso |
|---|---|
| **FastAPI** | API REST com documentação Swagger automática |
| **Streamlit** | Dashboard administrativo interativo |
| **SQLAlchemy** | ORM para banco de dados relacional |
| **SQLite** | Banco de dados (substituível por PostgreSQL) |
| **NLTK** | Processamento de Língua Natural |
| **Pydantic** | Validação de dados e schemas |
| **JWT + bcrypt** | Autenticação segura |
| **Plotly** | Visualizações interativas |
| **pytest** | Framework de testes |
| **Ruff** | Linter e formatador Python |

---

## Autor

**Jardel Vieira Alves**

---

## Licença

[MIT](LICENSE)
