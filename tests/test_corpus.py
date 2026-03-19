"""Testes de gerenciamento de corpus e documentos."""

from __future__ import annotations


def test_create_corpus(client, admin_token):
    """Cria um corpus via API."""
    r = client.post("/api/corpus/", json={
        "name": "Corpus Teste",
        "description": "Corpus para testes automatizados",
        "language": "pt",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Corpus Teste"
    assert data["document_count"] == 0


def test_list_corpora(client, admin_token):
    """Lista corpora do usuário."""
    client.post("/api/corpus/", json={"name": "C1"},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post("/api/corpus/", json={"name": "C2"},
                headers={"Authorization": f"Bearer {admin_token}"})

    r = client.get("/api/corpus/",
                   headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_upload_document(client, admin_token):
    """Envia um documento de texto para o corpus."""
    # Cria corpus
    r = client.post("/api/corpus/", json={"name": "Upload Test"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    corpus_id = r.json()["id"]

    # Upload
    content = "Este é um texto de teste para validação do upload de documentos."
    r = client.post(
        f"/api/corpus/{corpus_id}/documents",
        files={"file": ("test.txt", content.encode(), "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test.txt"
    assert data["token_count"] > 0


def test_list_documents(client, admin_token):
    """Lista documentos de um corpus."""
    r = client.post("/api/corpus/", json={"name": "Doc List Test"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    corpus_id = r.json()["id"]

    content = "Texto para teste de listagem."
    client.post(
        f"/api/corpus/{corpus_id}/documents",
        files={"file": ("doc1.txt", content.encode(), "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    r = client.get(f"/api/corpus/{corpus_id}/documents",
                   headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_validate_document(client, admin_token):
    """Valida um documento enviado."""
    r = client.post("/api/corpus/", json={"name": "Validation Test"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    corpus_id = r.json()["id"]

    content = "Texto para validação."
    r = client.post(
        f"/api/corpus/{corpus_id}/documents",
        files={"file": ("val.txt", content.encode(), "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    doc_id = r.json()["id"]

    r = client.patch(
        f"/api/corpus/{corpus_id}/documents/{doc_id}/validate",
        json={"status": "validado", "notes": "Aprovado no teste"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["validation_status"] == "validado"


def test_export_csv(client, admin_token):
    """Exporta metadados do corpus em CSV."""
    r = client.post("/api/corpus/", json={"name": "Export Test"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    corpus_id = r.json()["id"]

    client.post(
        f"/api/corpus/{corpus_id}/documents",
        files={"file": ("export.txt", b"Texto para exportacao.", "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    r = client.get(f"/api/corpus/{corpus_id}/export",
                   headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert "filename" in r.text
    assert "export.txt" in r.text


def test_delete_corpus(client, admin_token):
    """Remove um corpus e seus documentos."""
    r = client.post("/api/corpus/", json={"name": "Delete Test"},
                    headers={"Authorization": f"Bearer {admin_token}"})
    corpus_id = r.json()["id"]

    r = client.delete(f"/api/corpus/{corpus_id}",
                      headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 204

    r = client.get(f"/api/corpus/{corpus_id}",
                   headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 404
