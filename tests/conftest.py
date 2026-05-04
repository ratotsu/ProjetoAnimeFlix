"""
Configuração dos testes pytest.
Execute: pytest tests/ -v --cov=. --cov-report=html
"""

import pytest
from datetime import datetime
from main import app, db
from database import User, Series, Video, RefreshToken


@pytest.fixture(scope="function")
def test_app():
    """Cria aplicação de teste com banco em memória."""
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(test_app):
    """Cliente de teste Flask."""
    return test_app.test_client()


@pytest.fixture(scope="function")
def runner(test_app):
    """CLI runner para testes."""
    return test_app.test_cli_runner()


@pytest.fixture
def root_user(test_app):
    """Cria usuário root para testes."""
    with test_app.app_context():
        user = User(username="root", role="root")
        user.set_password("root123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(test_app):
    """Cria usuário admin para testes."""
    with test_app.app_context():
        user = User(username="admin", role="admin")
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def regular_user(test_app):
    """Cria usuário regular para testes."""
    with test_app.app_context():
        user = User(username="usuario", role="usuario")
        user.set_password("user123")
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_series(test_app):
    """Cria série de exemplo para testes."""
    with test_app.app_context():
        serie = Series(
            nome="Série Teste",
            descricao="Descrição da série teste",
            categoria="series"
        )
        db.session.add(serie)
        db.session.commit()
        return serie


@pytest.fixture
def sample_video(test_app, sample_series):
    """Cria vídeo de exemplo para testes."""
    with test_app.app_context():
        video = Video(
            yt_id="dQw4w9WgXcQ",
            titulo="Vídeo Teste",
            descricao="Descrição do vídeo teste",
            categoria="series",
            ano="2024",
            serie_id=sample_series.id,
            temporada="1",
            episodio="1"
        )
        db.session.add(video)
        db.session.commit()
        return video


@pytest.fixture
def auth_headers_root(client, root_user):
    """Retorna headers de autenticação para root."""
    response = client.post("/api/auth/login", json={
        "username": "root",
        "password": "root123"
    })
    data = response.get_json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def auth_headers_admin(client, admin_user):
    """Retorna headers de autenticação para admin."""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    data = response.get_json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def auth_headers_user(client, regular_user):
    """Retorna headers de autenticação para usuário regular."""
    response = client.post("/api/auth/login", json={
        "username": "usuario",
        "password": "user123"
    })
    data = response.get_json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "Content-Type": "application/json"
    }
