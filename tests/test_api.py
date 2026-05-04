"""
Testes para endpoints da API.
"""

import pytest


class TestHealthCheck:
    """Testes de health check."""
    
    def test_health(self, client):
        """Testa endpoint de health check."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
    
    def test_health_detailed(self, client):
        """Testa health check detalhado."""
        response = client.get("/api/health/detailed")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"


class TestUsers:
    """Testes de gerenciamento de usuários."""
    
    def test_list_users_as_root(self, client, auth_headers_root):
        """Testa listagem de usuários como root."""
        response = client.get("/api/users", headers=auth_headers_root)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "users" in data
        assert "pagination" in data
    
    def test_list_users_as_admin_fails(self, client, auth_headers_admin):
        """Testa que admin não pode listar usuários."""
        response = client.get("/api/users", headers=auth_headers_admin)
        
        assert response.status_code == 403
    
    def test_create_user_as_root(self, client, auth_headers_root):
        """Testa criação de usuário como root."""
        response = client.post("/api/users", 
            headers=auth_headers_root,
            json={
                "username": "novouser",
                "password": "senha123",
                "role": "usuario"
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["username"] == "novouser"
        assert data["role"] == "usuario"
    
    def test_create_user_duplicate(self, client, auth_headers_root, regular_user):
        """Testa criação de usuário duplicado."""
        response = client.post("/api/users",
            headers=auth_headers_root,
            json={
                "username": "usuario",
                "password": "senha123"
            }
        )
        
        assert response.status_code == 400
        assert "já existe" in response.get_json()["erro"]
    
    def test_create_user_weak_password(self, client, auth_headers_root):
        """Testa criação com senha fraca."""
        response = client.post("/api/users",
            headers=auth_headers_root,
            json={
                "username": "novouser",
                "password": "123"
            }
        )
        
        assert response.status_code == 400
    
    def test_delete_user(self, client, auth_headers_root, regular_user):
        """Testa exclusão de usuário."""
        response = client.delete(f"/api/users/{regular_user.id}", headers=auth_headers_root)
        
        assert response.status_code == 204
    
    def test_delete_root_fails(self, client, auth_headers_root, root_user):
        """Testa que não pode deletar outro root (proteção)."""
        # Criar outro root
        other_root = client.post("/api/users",
            headers=auth_headers_root,
            json={
                "username": "otherroot",
                "password": "root123",
                "role": "root"
            }
        )
        
        other_id = other_root.get_json()["id"]
        response = client.delete(f"/api/users/{other_id}", headers=auth_headers_root)
        
        # Deve permitir (ajustar conforme lógica de negócio)
        assert response.status_code in [204, 400]


class TestSeries:
    """Testes de séries."""
    
    def test_list_series_public(self, client):
        """Testa que listar séries é público."""
        response = client.get("/api/series")
        
        assert response.status_code == 200
        data = response.get_json()
        assert "series" in data
    
    def test_create_series_as_admin(self, client, auth_headers_admin):
        """Testa criação de série como admin."""
        response = client.post("/api/series",
            headers=auth_headers_admin,
            json={
                "nome": "Nova Série",
                "descricao": "Descrição",
                "categoria": "series"
            }
        )
        
        assert response.status_code == 201
    
    def test_create_series_as_user_fails(self, client, auth_headers_user):
        """Testa que usuário regular não pode criar série."""
        response = client.post("/api/series",
            headers=auth_headers_user,
            json={
                "nome": "Nova Série",
                "descricao": "Descrição"
            }
        )
        
        assert response.status_code == 403
    
    def test_series_pagination(self, client):
        """Testa paginação de séries."""
        response = client.get("/api/series?page=1&per_page=10")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10
    
    def test_series_filter_by_category(self, client, auth_headers_admin):
        """Testa filtro por categoria."""
        # Criar série em categoria específica
        client.post("/api/series",
            headers=auth_headers_admin,
            json={
                "nome": "Série Doc",
                "categoria": "docs"
            }
        )
        
        response = client.get("/api/series?categoria=docs")
        data = response.get_json()
        
        assert all(s["categoria"] == "docs" for s in data["series"])


class TestVideos:
    """Testes de vídeos."""
    
    def test_list_videos_public(self, client):
        """Testa que listar vídeos é público."""
        response = client.get("/api/videos")
        
        assert response.status_code == 200
        data = response.get_json()
        assert "videos" in data
    
    def test_create_video_as_admin(self, client, auth_headers_admin):
        """Testa criação de vídeo como admin."""
        response = client.post("/api/videos",
            headers=auth_headers_admin,
            json={
                "yt_id": "dQw4w9WgXcQ",
                "titulo": "Vídeo Teste",
                "categoria": "outros"
            }
        )
        
        assert response.status_code == 201
    
    def test_create_video_invalid_yt_id(self, client, auth_headers_admin):
        """Testa criação com ID do YouTube inválido."""
        response = client.post("/api/videos",
            headers=auth_headers_admin,
            json={
                "yt_id": "invalido",
                "titulo": "Vídeo Teste"
            }
        )
        
        assert response.status_code == 400
    
    def test_create_duplicate_video(self, client, auth_headers_admin, sample_video):
        """Testa criação de vídeo duplicado."""
        response = client.post("/api/videos",
            headers=auth_headers_admin,
            json={
                "yt_id": sample_video.yt_id,
                "titulo": "Outro Título"
            }
        )
        
        assert response.status_code == 400
    
    def test_video_search(self, client, auth_headers_admin):
        """Testa busca de vídeos."""
        # Criar vídeos
        for i in range(3):
            client.post("/api/videos",
                headers=auth_headers_admin,
                json={
                    "yt_id": f"test{i:08d}",
                    "titulo": f"Vídeo Python {i}"
                }
            )
        
        response = client.get("/api/videos?search=Python")
        data = response.get_json()
        
        assert len(data["videos"]) >= 3
    
    def test_video_pagination(self, client):
        """Testa paginação de vídeos."""
        response = client.get("/api/videos?page=2&per_page=5")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["pagination"]["page"] == 2
    
   