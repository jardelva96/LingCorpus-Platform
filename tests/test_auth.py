"""Testes de autenticação e controle de acesso."""

from __future__ import annotations


def test_register_user(client):
    """Registra um novo usuário via API."""
    r = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "new@test.com",
        "password": "secret123",
        "full_name": "New User",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "newuser"
    assert data["role"] == "visitante"


def test_register_duplicate_username(client, admin_user):
    """Rejeita cadastro com username duplicado."""
    r = client.post("/api/auth/register", json={
        "username": "testadmin",
        "email": "other@test.com",
        "password": "secret123",
        "full_name": "Other",
    })
    assert r.status_code == 400
    assert "já existe" in r.json()["detail"]


def test_login_success(client, admin_user):
    """Login com credenciais válidas retorna token."""
    r = client.post("/api/auth/login",
                    data={"username": "testadmin", "password": "testpass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client, admin_user):
    """Login com senha incorreta retorna 401."""
    r = client.post("/api/auth/login",
                    data={"username": "testadmin", "password": "wrong"})
    assert r.status_code == 401


def test_get_me(client, admin_token):
    """Endpoint /me retorna dados do usuário autenticado."""
    r = client.get("/api/auth/me",
                   headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "testadmin"
    assert r.json()["role"] == "admin"


def test_unauthorized_access(client):
    """Acesso sem token retorna 401."""
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_list_users_admin_only(client, admin_token, researcher_token):
    """Apenas admin pode listar todos os usuários."""
    r = client.get("/api/users/",
                   headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200

    r = client.get("/api/users/",
                   headers={"Authorization": f"Bearer {researcher_token}"})
    assert r.status_code == 403


def test_update_user_role(client, admin_token, researcher_user):
    """Admin pode alterar papel de outro usuário."""
    r = client.patch(
        f"/api/users/{researcher_user.id}",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "admin"
