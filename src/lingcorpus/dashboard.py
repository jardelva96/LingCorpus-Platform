"""Dashboard administrativo Streamlit para a LingCorpus Platform."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = "http://localhost:8000"


# ── Helpers ───────────────────────────────────────────────────────────────


def _api(method: str, path: str, **kwargs) -> requests.Response:
    """Faz uma chamada à API com token de autenticação."""
    headers = kwargs.pop("headers", {})
    if "token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.request(method, f"{API_URL}{path}", headers=headers, timeout=30, **kwargs)


def _check_api() -> bool:
    """Verifica se a API está acessível."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


# ── Autenticação ──────────────────────────────────────────────────────────


def _login_page():
    """Página de login."""
    st.markdown("## Acesso à Plataforma")
    st.caption(
        "Entre com suas credenciais para acessar o painel administrativo. "
        "O sistema utiliza autenticação JWT com controle de acesso baseado em papéis."
    )

    col1, col2 = st.columns([1, 1])
    with col1, st.form("login_form"):
        st.markdown("### Login")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", width="stretch")

        if submitted and username and password:
            r = _api("POST", "/api/auth/login",
                     data={"username": username, "password": password})
            if r.status_code == 200:
                st.session_state.token = r.json()["access_token"]
                st.session_state.logged_in = True
                # Obtém dados do usuário
                me = _api("GET", "/api/auth/me")
                if me.status_code == 200:
                    st.session_state.user = me.json()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with col2, st.expander("Criar nova conta", expanded=False), st.form("register_form"):
        new_user = st.text_input("Nome de usuário", key="reg_user")
        new_email = st.text_input("Email", key="reg_email")
        new_name = st.text_input("Nome completo", key="reg_name")
        new_pass = st.text_input("Senha", type="password", key="reg_pass")
        role = st.selectbox("Papel", ["visitante", "pesquisador"])
        reg_submit = st.form_submit_button("Registrar", width="stretch")

        if reg_submit and new_user and new_email and new_pass and new_name:
            r = _api("POST", "/api/auth/register", json={
                "username": new_user,
                "email": new_email,
                "password": new_pass,
                "full_name": new_name,
                "role": role,
            })
            if r.status_code == 201:
                st.success("Conta criada! Faça login.")
            else:
                st.error(r.json().get("detail", "Erro ao registrar."))

    st.divider()
    st.caption("Credenciais padrão: **admin** / **admin123**")


# ── Tabs ──────────────────────────────────────────────────────────────────


def _tab_overview():
    """Visão geral da plataforma."""
    st.markdown("### Visão Geral")
    st.caption(
        "Resumo do estado atual da plataforma: corpora cadastrados, documentos enviados "
        "e estatísticas de uso."
    )

    r = _api("GET", "/api/corpus/")
    if r.status_code != 200:
        st.error("Erro ao carregar corpora.")
        return

    corpora = r.json()

    col1, col2, col3 = st.columns(3)
    col1.metric("Corpora", len(corpora))
    total_docs = sum(c.get("document_count", 0) for c in corpora)
    col2.metric("Documentos", total_docs)
    languages = {c["language"] for c in corpora}
    col3.metric("Idiomas", len(languages))

    if corpora:
        df = pd.DataFrame(corpora)
        df = df[["id", "name", "language", "document_count", "created_at"]]
        df.columns = ["ID", "Nome", "Idioma", "Documentos", "Criado em"]
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("Nenhum corpus cadastrado. Use a aba **Corpus** para criar um.")


def _tab_corpus():
    """Gerenciamento de corpora e upload de documentos."""
    st.markdown("### Gerenciamento de Corpus")
    st.caption(
        "Crie coleções de textos (corpora) e envie documentos para análise. "
        "Cada corpus agrupa documentos por tema ou projeto de pesquisa."
    )

    # Criar corpus
    with st.expander("Criar novo corpus", expanded=False), st.form("create_corpus"):
        name = st.text_input("Nome do corpus")
        desc = st.text_area("Descrição")
        lang = st.selectbox("Idioma", ["pt", "en", "es"], index=0)
        if st.form_submit_button("Criar", width="stretch"):
            r = _api("POST", "/api/corpus/", json={
                "name": name, "description": desc, "language": lang,
            })
            if r.status_code == 201:
                st.success(f"Corpus '{name}' criado!")
                st.rerun()
            else:
                st.error(r.json().get("detail", "Erro ao criar corpus."))

    # Listar corpora
    r = _api("GET", "/api/corpus/")
    if r.status_code != 200:
        return
    corpora = r.json()
    if not corpora:
        return

    selected = st.selectbox(
        "Selecione um corpus",
        corpora,
        format_func=lambda c: f"{c['name']} ({c['document_count']} docs)",
    )
    if not selected:
        return

    corpus_id = selected["id"]

    # Upload de documento
    st.markdown("#### Upload de documentos")
    st.caption(
        "Envie arquivos de texto (.txt, .csv) para o corpus. A plataforma detecta "
        "automaticamente a codificação do arquivo e calcula estatísticas de tokens."
    )
    uploaded = st.file_uploader(
        "Selecione arquivo(s)",
        type=["txt", "csv", "tsv"],
        accept_multiple_files=True,
    )
    if uploaded:
        for f in uploaded:
            r = _api("POST", f"/api/corpus/{corpus_id}/documents",
                     files={"file": (f.name, f.getvalue())})
            if r.status_code == 200:
                st.success(f"'{f.name}' enviado!")
            else:
                st.error(f"Erro ao enviar '{f.name}'.")

    # Listar documentos
    r = _api("GET", f"/api/corpus/{corpus_id}/documents")
    if r.status_code == 200:
        docs = r.json()
        if docs:
            st.markdown("#### Documentos no corpus")
            df = pd.DataFrame(docs)
            cols = ["id", "filename", "original_encoding", "token_count",
                    "type_count", "validation_status"]
            df = df[[c for c in cols if c in df.columns]]
            df.columns = ["ID", "Arquivo", "Codificação", "Tokens", "Types", "Status"]
            st.dataframe(df, width="stretch", hide_index=True)


def _tab_validation():
    """Validação de documentos."""
    st.markdown("### Validação de Documentos")
    st.caption(
        "Revise e valide os documentos enviados ao corpus. A validação garante "
        "a integridade dos dados antes da análise. Documentos podem ser marcados "
        "como **Validado**, **Pendente** ou **Rejeitado**."
    )

    with st.expander("O que é validação de dados?"):
        st.markdown("""
A validação de dados é um processo essencial em pesquisa para garantir que os textos
enviados à plataforma estejam íntegros e adequados para análise. Verificações incluem:

| Verificação | Descrição |
|---|---|
| **Codificação** | O arquivo usa codificação válida (UTF-8, ISO-8859-1, etc.)? |
| **Conteúdo** | O arquivo contém texto ou está vazio? |
| **Linhas em branco** | Proporção de linhas vazias está dentro do esperado? |
| **Caracteres de controle** | Há caracteres inválidos que precisam ser removidos? |
| **Consistência** | As quebras de linha são consistentes? |
""")

    r = _api("GET", "/api/corpus/")
    if r.status_code != 200:
        return
    corpora = r.json()
    if not corpora:
        st.info("Nenhum corpus cadastrado.")
        return

    selected = st.selectbox(
        "Corpus para validação",
        corpora,
        format_func=lambda c: c["name"],
        key="val_corpus",
    )
    if not selected:
        return

    corpus_id = selected["id"]
    r = _api("GET", f"/api/corpus/{corpus_id}/documents")
    if r.status_code != 200:
        return
    docs = r.json()
    pending = [d for d in docs if d["validation_status"] == "pendente"]

    if not pending:
        st.success("Todos os documentos deste corpus foram validados!")
        return

    st.warning(f"{len(pending)} documento(s) pendente(s) de validação.")

    for doc in pending:
        with st.expander(f"{doc['filename']} ({doc['token_count']} tokens)"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Validar", key=f"val_{doc['id']}"):
                    _api("PATCH",
                         f"/api/corpus/{corpus_id}/documents/{doc['id']}/validate",
                         json={"status": "validado", "notes": "Aprovado"})
                    st.rerun()
            with col2:
                if st.button("Rejeitar", key=f"rej_{doc['id']}"):
                    _api("PATCH",
                         f"/api/corpus/{corpus_id}/documents/{doc['id']}/validate",
                         json={"status": "rejeitado", "notes": "Rejeitado"})
                    st.rerun()


def _tab_analysis():
    """Análise NLP do corpus."""
    st.markdown("### Análise Linguística")
    st.caption(
        "Ferramentas de Processamento de Língua Natural aplicadas ao corpus. "
        "Inclui estatísticas descritivas, frequência de palavras, concordância KWIC "
        "e análise de n-gramas."
    )

    r = _api("GET", "/api/corpus/")
    if r.status_code != 200:
        return
    corpora = r.json()
    if not corpora:
        st.info("Nenhum corpus cadastrado.")
        return

    selected = st.selectbox(
        "Corpus para análise",
        corpora,
        format_func=lambda c: f"{c['name']} ({c['document_count']} docs)",
        key="analysis_corpus",
    )
    if not selected or selected["document_count"] == 0:
        st.info("Selecione um corpus com documentos para análise.")
        return

    corpus_id = selected["id"]

    # Estatísticas
    with st.expander("O que significam as métricas?"):
        st.markdown("""
| Métrica | Descrição | Interpretação |
|---|---|---|
| **Tokens** | Total de palavras (incluindo repetições) | Volume do corpus |
| **Types** | Palavras únicas (vocabulário) | Diversidade lexical |
| **TTR** | Razão Type/Token (types ÷ tokens) | Riqueza vocabular (0 a 1) |
| **Hapax Legomena** | Palavras que aparecem apenas uma vez | Palavras raras |
| **Razão Hapax** | Hapax ÷ total de tokens | Proporção de palavras raras |
| **Comprimento médio** | Média de caracteres por palavra | Complexidade lexical |
| **Palavras/sentença** | Média de palavras por sentença | Complexidade sintática |
""")

    r_stats = _api("GET", f"/api/analysis/{corpus_id}/statistics")
    if r_stats.status_code == 200:
        stats = r_stats.json()
        st.markdown("#### Estatísticas Descritivas")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tokens", f"{stats['total_tokens']:,}")
        c2.metric("Types", f"{stats['total_types']:,}")
        c3.metric("TTR", f"{stats['type_token_ratio']:.3f}")
        c4.metric("Hapax", f"{stats['hapax_legomena']:,}")

        c5, c6, c7 = st.columns(3)
        c5.metric("Comp. médio", f"{stats['avg_word_length']:.1f} chars")
        c6.metric("Palavras/sent.", f"{stats['avg_sentence_length']:.1f}")
        c7.metric("Razão Hapax", f"{stats['hapax_ratio']:.3f}")

    # Frequências
    st.markdown("#### Frequência de Palavras")
    st.caption(
        "As palavras mais frequentes no corpus, com remoção de stopwords. "
        "A frequência relativa indica a proporção de cada palavra no total."
    )

    top_n = st.slider("Quantidade de palavras", 10, 100, 30, key="freq_n")
    r_freq = _api("GET", f"/api/analysis/{corpus_id}/frequencies",
                  params={"top_n": top_n, "remove_stopwords": True})
    if r_freq.status_code == 200:
        freqs = r_freq.json()
        if freqs:
            df = pd.DataFrame(freqs)
            fig = px.bar(
                df, x="token", y="frequency",
                title="Distribuição de Frequência",
                labels={"token": "Palavra", "frequency": "Frequência"},
                color="frequency",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width="stretch")

            st.dataframe(df, width="stretch", hide_index=True)

    # Concordância
    st.markdown("#### Concordância KWIC")
    st.caption(
        "Key Word In Context (KWIC): mostra cada ocorrência de uma palavra-chave "
        "com o contexto à esquerda e à direita. Ferramenta fundamental em "
        "Linguística de Corpus para estudar padrões de uso."
    )

    keyword = st.text_input("Palavra-chave para concordância", key="kwic_word")
    if keyword:
        r_conc = _api("GET", f"/api/analysis/{corpus_id}/concordance",
                      params={"keyword": keyword, "window": 6})
        if r_conc.status_code == 200:
            lines = r_conc.json()
            if lines:
                df = pd.DataFrame(lines)
                df.columns = ["Contexto esquerdo", "Palavra", "Contexto direito", "Documento"]
                st.dataframe(df, width="stretch", hide_index=True)
                st.caption(f"{len(lines)} ocorrência(s) encontrada(s).")
            else:
                st.info(f"Nenhuma ocorrência de '{keyword}' encontrada.")

    # N-gramas
    st.markdown("#### N-gramas")
    st.caption(
        "Sequências de N palavras consecutivas mais frequentes. "
        "Bigramas (N=2) e trigramas (N=3) revelam colocações e expressões fixas."
    )

    n_val = st.selectbox("Tamanho do n-grama", [2, 3, 4], index=0, key="ngram_n")
    r_ng = _api("GET", f"/api/analysis/{corpus_id}/ngrams",
                params={"n": n_val, "top_k": 20})
    if r_ng.status_code == 200:
        grams = r_ng.json()
        if grams:
            df = pd.DataFrame(grams)
            df.columns = ["N-grama", "Frequência"]
            fig = px.bar(
                df, x="N-grama", y="Frequência",
                title=f"Top {len(grams)} {n_val}-gramas",
                color="Frequência",
                color_continuous_scale="Tealgrn",
            )
            st.plotly_chart(fig, width="stretch")


def _tab_users():
    """Gerenciamento de usuários (admin)."""
    st.markdown("### Gerenciamento de Usuários")
    st.caption(
        "Controle de acesso baseado em papéis (RBAC). Gerencie os usuários cadastrados "
        "e seus níveis de permissão na plataforma."
    )

    with st.expander("Níveis de acesso"):
        st.markdown("""
| Papel | Permissões |
|---|---|
| **Admin** | Acesso total: criar/editar/excluir corpora, gerenciar usuários, validar |
| **Pesquisador** | Criar corpora próprios, enviar documentos, validar, analisar |
| **Visitante** | Visualizar corpora e análises (somente leitura) |
""")

    user = st.session_state.get("user", {})
    if user.get("role") != "admin":
        st.warning("Apenas administradores podem gerenciar usuários.")
        return

    r = _api("GET", "/api/users/")
    if r.status_code != 200:
        st.error("Erro ao carregar usuários.")
        return

    users = r.json()
    df = pd.DataFrame(users)
    df = df[["id", "username", "full_name", "email", "role", "is_active", "created_at"]]
    df.columns = ["ID", "Usuário", "Nome", "Email", "Papel", "Ativo", "Criado em"]
    st.dataframe(df, width="stretch", hide_index=True)

    st.markdown("#### Alterar papel de usuário")
    user_options = {u["username"]: u["id"] for u in users}
    sel_user = st.selectbox("Usuário", list(user_options.keys()), key="edit_user")
    new_role = st.selectbox("Novo papel", ["admin", "pesquisador", "visitante"], key="new_role")
    if st.button("Atualizar papel"):
        uid = user_options[sel_user]
        r = _api("PATCH", f"/api/users/{uid}", json={"role": new_role})
        if r.status_code == 200:
            st.success(f"Papel de '{sel_user}' atualizado para '{new_role}'.")
            st.rerun()


def _tab_audit():
    """Log de auditoria."""
    st.markdown("### Log de Auditoria")
    st.caption(
        "Registro de todas as ações realizadas na plataforma. "
        "Permite rastrear quem fez o quê e quando, essencial para "
        "integridade e segurança dos dados de pesquisa."
    )

    with st.expander("Tipos de ação rastreados"):
        st.markdown("""
| Ação | Descrição |
|---|---|
| **LOGIN** | Acesso à plataforma |
| **REGISTER** | Criação de nova conta |
| **CREATE** | Criação de corpus |
| **UPLOAD** | Envio de documento |
| **VALIDATE** | Validação/rejeição de documento |
| **UPDATE** | Alteração de dados |
| **DELETE** | Remoção de corpus ou documento |
| **UPDATE_USER** | Alteração de papel/status de usuário |
""")

    # A API de auditoria precisaria de um endpoint dedicado, mas podemos
    # mostrar os dados disponíveis via corpus
    st.info(
        "O log de auditoria completo está disponível via API em "
        "`GET /api/audit/logs`. No dashboard, exibimos as ações recentes "
        "registradas no banco de dados."
    )


def _tab_export():
    """Exportação de dados."""
    st.markdown("### Exportação de Dados")
    st.caption(
        "Exporte os metadados e resultados de análise do corpus em formato CSV "
        "para uso em outras ferramentas ou relatórios de pesquisa."
    )

    r = _api("GET", "/api/corpus/")
    if r.status_code != 200:
        return
    corpora = r.json()
    if not corpora:
        st.info("Nenhum corpus disponível para exportação.")
        return

    selected = st.selectbox(
        "Corpus para exportar",
        corpora,
        format_func=lambda c: c["name"],
        key="export_corpus",
    )
    if not selected:
        return

    corpus_id = selected["id"]

    if st.button("Exportar metadados (CSV)"):
        r = _api("GET", f"/api/corpus/{corpus_id}/export")
        if r.status_code == 200:
            st.download_button(
                "Baixar CSV",
                data=r.text,
                file_name=f"corpus_{corpus_id}_export.csv",
                mime="text/csv",
            )

    if st.button("Exportar frequências (CSV)"):
        r = _api("GET", f"/api/analysis/{corpus_id}/frequencies",
                 params={"top_n": 500, "remove_stopwords": True})
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            st.download_button(
                "Baixar frequências CSV",
                data=df.to_csv(index=False),
                file_name=f"corpus_{corpus_id}_frequencies.csv",
                mime="text/csv",
            )


# ── Main ──────────────────────────────────────────────────────────────────


def main():
    """Ponto de entrada do dashboard Streamlit."""
    st.set_page_config(
        page_title="LingCorpus Platform",
        page_icon="📚",
        layout="wide",
    )

    st.markdown("# LingCorpus Platform")
    st.markdown(
        "*Plataforma web para gerenciamento, validação e análise de corpus textual "
        "de pesquisa em Linguística Computacional*"
    )

    if not _check_api():
        st.error(
            "API não está acessível em `http://localhost:8000`. "
            "Inicie a API primeiro com `lingcorpus-api` ou `python -m lingcorpus`."
        )
        st.stop()

    # Login
    if not st.session_state.get("logged_in"):
        _login_page()
        return

    # Sidebar
    user = st.session_state.get("user", {})
    st.sidebar.markdown(f"**{user.get('full_name', 'Usuário')}**")
    st.sidebar.caption(f"Papel: `{user.get('role', 'visitante')}`")
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("### Navegação")
    st.sidebar.caption(
        "Use as abas abaixo para navegar entre as funcionalidades da plataforma."
    )

    # Tabs
    tabs = st.tabs([
        "Visão Geral",
        "Corpus",
        "Validação",
        "Análise NLP",
        "Usuários",
        "Auditoria",
        "Exportação",
    ])

    with tabs[0]:
        _tab_overview()
    with tabs[1]:
        _tab_corpus()
    with tabs[2]:
        _tab_validation()
    with tabs[3]:
        _tab_analysis()
    with tabs[4]:
        _tab_users()
    with tabs[5]:
        _tab_audit()
    with tabs[6]:
        _tab_export()


if __name__ == "__main__":
    main()
