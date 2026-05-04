"""
Testes para autenticação JWT.
"""

import pytest
import time
from datetime import datetime, timedelta


class TestAuthLogin:
    """Testes de login."""
    
    def test_login_success(self, client, root_user):
        """Testa login com credenciais válidas."""
        response = client.post("/api/auth/login", json={
            "username": "root",
            "password": "root123"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["user"]["username"] == "root"
        assert data["user"]["role"] == "root"
    
    def test_login_invalid_credentials(self, client, root_user):
        """Testa login com credenciais inválidas."""
        response = client.post("/api/auth/login", json={
            "username": "root",
            "password": "senha_errada"
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert "erro" in data
    
    def test_login_nonexistent_user(self, client):
        """Testa login com usuário inexistente."""
        response = client.post("/api/auth/login", json={
            "username": "naoexiste",
            "password": "qualquer"
        })
        
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client):
        """Testalogin com campos faltando."""
        # Sem senha
        response = client.post("/api/auth/login", json={
            "username": "root"
        })
        assert response.status_code == 400
        
        # Sem username
        response = client.post("/api/auth/login", json={
            "password": "root123"
        })
        assert response.status_code == 400
        
        # JSON vazio
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 400
    
    def test_login_basic_auth_header(self, client, root_user):
        """Testa login via Basic Auth header."""
        import base64
        credentials = base64.b64encode(b"root:root123").decode()
        
        response = client.post("/api/auth/login", headers={
            "Authorization": f"Basic {credentials}"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.get_json()


class TestAuthRefresh:
    """Testes de refresh token."""
    
    def test_refresh_success(self, client, root_user):
        """Testa renovação de token com refresh token válido."""
        # Login primeiro
        login_response = client.post("/api/auth/login", json={
            "username": "root",
            "password": "root123"
        })
        refresh_token = login_response.get_json()["refresh_token"]
        
        # Renovar token
        response = client.post("/api/auth/refresh", headers={
            "Authorization": f"Bearer {refresh_token}"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
    
    def test_refresh_with_access_token_fails(self, client, root_user):
        """Testa que access token não pode ser usado para refresh."""
        login_response = client.post("/api/auth/login", json={
            "username": "root",
            "password": "root123"
        })
        access_token = login_response.get_json()["access_token"]
        
        response = client.post("/api/auth/refresh", headers={
            "Authorization": f"Bearer {access_token}"
        })
        
        assert response.status_code == 422


class TestAuthLogout:
    """Testes de logout."""
    
    def test_logout_success(self, client, root_user):
        """Testa logout revogando access token."""
        # Login
        login_response = client.post("/api/auth/login", json={
            "username": "root",
            "password": "root123"
        })
        access_token = login_response.get_json()["access_token"]
        
        # Logout
        response = client.post("/api/auth/logout", headers={
            "Authorization": f"Bearer {access_token}"
        })
        
        assert response.status_code == 200
        
        # Tentar usar token revogado
        me_response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        assert me_response.status_code == 401
    
    def test_logout_all_sessions(self, client, root_user):
        """Testa logout de todas as sessões."""
        # Múltiplos logins
        tokens = []
        for _ in range(3):
            resp = client.post("/api/auth/login", json={
                "username": "root",
                "password": "root123"
            })
            tokens.append(resp.get_json()["access_token"])
        
        # Logout all
        response = client.post("/api/auth/logout-all", headers={
            "Authorization": f"Bearer {tokens[0]}"
        })
        
        assert response.status_code == 200
        
        # Verificar que tokens foram revogados
        for token in tokens[1:]:
            me_response = client.get("/api/auth/me", headers={
                "Authorization": f"Bearer {token}"
            })
            assert me_response.status_code == 401


class TestAuthMe:
    """Testes do endpoint /me."""
    
    def test_get_current_user(self, client, auth_headers_root, root_user):
        """Testa obtenção do usuário atual."""
        response = client.get("/api/auth/me", headers=auth_headers_root)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["username"] == "root"
        assert data["role"] == "root"
    
    def test_get_current_user_no_token(self, client):
        """Testa que endpoint requer autenticação."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """Testa com token inválido."""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer token_invalido"
        })
        
        assert response.status_code == 401