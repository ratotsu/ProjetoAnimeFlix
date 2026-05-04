"""
StreamFlix - API com HTTPS Obrigatório e Segurança Aprimorada
================================================================

Funcionalidades de segurança:
- Redirecionamento automático HTTP → HTTPS
- HSTS (HTTP Strict Transport Security) com preload
- Headers de segurança TLS 1.3
- Content Security Policy
- Proteção contra clickjacking, XSS, MIME sniffing
"""

import base64
import os
import re
import ssl
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman  # Para headers de segurança

from database import db, User, Video, Series
from dlp_playlist import extract_playlist_entries, extrair_yt_id

# --- Configurações ---

ROLE_LEVEL = {
    "usuario": 1,
    "admin": 2,
    "root": 3,
}

VALID_CATEGORIES = {"filmes", "series", "docs", "outros"}

# Acessa variáveis de ambiente
FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "false").lower() == "true"
ENVIRONMENT = os.environ.get("FLASK_ENV", "development")

# --- Aplicação ---

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///streamflix.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "secret-key-change-in-production")

# --- Configuração CORS ---
CORS(app, 
     origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000,https://localhost:5443,https://127.0.0.1:5443").split(","),
     allow_headers=["Authorization", "Content-Type"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

# --- Rate Limiting ---
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# --- Flask-Talisman para Segurança HTTPS ---
# Configuração de CSP (Content Security Policy)
csp = {
    'default-src': '\'self\'',
    'img-src': ['\'self\'', 'https://img.youtube.com', 'https://i.ytimg.com', 'data:'],
    'frame-src': ['\'self\'', 'https://www.youtube.com', 'https://youtube.com'],
    'script-src': ['\'self\'', '\'unsafe-inline\''],
    'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://fonts.googleapis.com'],
    'font-src': ['\'self\'', 'https://fonts.gstatic.com'],
    'connect-src': '\'self\'',
}

# Inicializar Talman APENAS em produção (para forçar HTTPS e headers de segurança)
if ENVIRONMENT == "production" or FORCE_HTTPS:
    Talisman(
        app,
        force_https=True,
        force_https_permanent=True,  # 301 redirect
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,  # 1 year
        strict_transport_security_include_subdomains=True,
        strict_transport_security_preload=True,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        session_cookie_secure=True,
        session_cookie_httponly=True,
    )

db.init_app(app)

# ============================================
# MIDDLEWARE DE REDIRECIONAMENTO HTTPS
# ============================================

@app.before_request
def enforce_https():
    """
    Força redirecionamento HTTPS em produção.
    Roda ANTES de cada request.
    """
    if ENVIRONMENT == "production" or FORCE_HTTPS:
        # Verificar se a request é HTTPS
        if not request.is_secure and request.headers.get("X-Forwarded-Proto", "http") != "https":
            # Redirecionar para HTTPS
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

@app.before_request
def add_security_headers():
    """Adiciona headers de segurança em TODAS as responses."""
    pass  # Feito pelo @app.after_request

@app.after_request
def _add_security_headers(response):
    """
    Adiciona headers de segurança robustos em todas as responses.
    Compatível com TLS 1.3 e proteções modernas.
    """
    # --- Segurança Básica ---
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    
    # --- HSTS (HTTP Strict Transport Security) ---
    # max-age=31536000 = 1 ano
    # includeSubDomains = aplica a todos os subdomínios
    # preload = elegível para HSTS preload list dos navegadores
    if ENVIRONMENT == "production" or FORCE_HTTPS:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # --- Content Security Policy (se Talisman não estiver ativo) ---
    if not (ENVIRONMENT == "production" or FORCE_HTTPS):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' https://img.youtube.com https://i.ytimg.com data:; "
            "frame-src 'self' https://www.youtube.com https://youtube.com; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'"
        )
    
    # --- Indicadores de Segurança ---
    response.headers["X-DNS-Prefetch-Control"] = "off"
    response.headers["X-Download-Options"] = "noopen"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    
    # Remover header "Server" para não expor tecnologia
    response.headers.pop("Server", None)
    
    return response

# ============================================
# AUTENTICAÇÃO (Basic Auth - será substituída por JWT em breve)
# ============================================

def get_authenticated_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("basic "):
        return None

    try:
        token = auth_header.split(None, 1)[1]
        decoded = base64.b64decode(token).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return None

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return None
    return user

def require_role(min_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_authenticated_user()
            if not user:
                return jsonify({"erro": "Credenciais inválidas"}), 401
            if ROLE_LEVEL.get(user.role, 0) < ROLE_LEVEL.get(min_role, 0):
                return jsonify({"erro": "Acesso não autorizado"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ============================================
# VALIDAÇÃO DE DADOS
# ============================================

def validar_entrada_texto(texto, max_length=200, allow_empty=False):
    """Valida entrada de texto contra XSS e outros ataques."""
    if texto is None:
        return allow_empty
    if not isinstance(texto, str):
        return False
    if len(texto) > max_length:
        return False
    if re.search(r'[<>"\'\\]', texto):
        return False
    return True

# ============================================
# INICIALIZAÇÃO
# ============================================

def ensure_root_user_exists():
    """Cria o usuário root padrão se não existir."""
    if User.query.filter_by(role="root").first() is None:
        root_password = os.environ.get("ROOT_PASSWORD", "root123")
        root = User(username="root", role="root")
        root.set_password(root_password)
        db.session.add(root)
        db.session.commit()
        print(f"[INIT] Usuário root criado: {root.username}")

with app.app_context():
    db.create_all()
    ensure_root_user_exists()

# ============================================
# ROTAS PÚBLICAS
# ============================================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/health")
def health_check():
    """Endpoint de health check."""
    return jsonify({
        "status": "healthy",
        "environment": ENVIRONMENT,
        "https": request.is_secure,
        "timestamp": datetime.utcnow().isoformat()
    })

# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    user = get_authenticated_user()
    if not user:
        return jsonify({"erro": "Credenciais inválidas"}), 401
    return jsonify(user.to_dict())

# ============================================
# ROTAS DE USUÁRIOS (ROOT ONLY)
# ============================================

@app.route("/api/users", methods=["GET"])
@require_role("root")
def listar_usuarios():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([user.to_dict() for user in users])

@app.route("/api/users", methods=["POST"])
@require_role("root")
def criar_usuario():
    dados = request.get_json() or {}
    username = (dados.get("username") or "").strip()
    password = dados.get("password") or ""
    role = dados.get("role", "usuario")

    if not validar_entrada_texto(username, 80) or not username:
        return jsonify({"erro": "Usuário inválido"}), 400
    if not password or len(password) < 6:
        return jsonify({"erro": "Senha deve ter pelo menos 6 caracteres"}), 400
    if role not in ROLE_LEVEL:
        return jsonify({"erro": "Nível de acesso inválido"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"erro": "Nome de usuário já existe"}), 400

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@app.route("/api/users/<int:user_id>", methods=["PUT"])
@require_role("root")
def atualizar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    dados = request.get_json() or {}
    if "password" in dados and dados["password"]:
        user.set_password(dados["password"])
    if "role" in dados and dados["role"] in ROLE_LEVEL:
        user.role = dados["role"]
    db.session.commit()
    return jsonify(user.to_dict())

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@require_role("root")
def deletar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return "", 204

# ============================================
# ROTAS DE SÉRIES
# ============================================

@app.route("/api/series", methods=["GET"])
def listar_series():
    categoria = request.args.get("categoria")
    query = Series.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    series = query.order_by(Series.id.desc()).all()
    return jsonify([serie.to_dict() for serie in series])

@app.route("/api/series/<int:serie_id>", methods=["GET"])
def buscar_serie(serie_id):
    serie = Series.query.get_or_404(serie_id)
    return jsonify(serie.to_dict())

@app.route("/api/series", methods=["POST"])
@require_role("admin")
def criar_serie():
    dados = request.get_json() or {}
    nome = (dados.get("nome") or "").strip()
    if not validar_entrada_texto(nome, 200) or not nome:
        return jsonify({"erro": "Nome da série inválido"}), 400
    if Series.query.filter_by(nome=nome).first():
        return jsonify({"erro": "Série já cadastrada"}), 400

    descricao = dados.get("descricao", "")
    if not validar_entrada_texto(descricao, 2000, allow_empty=True):
        return jsonify({"erro": "Descrição inválida"}), 400

    serie = Series(
        nome=nome,
        descricao=descricao,
        categoria=dados.get("categoria", "series"),
    )
    db.session.add(serie)
    db.session.commit()
    return jsonify(serie.to_dict()), 201

@app.route("/api/series/<int:serie_id>", methods=["PUT"])
@require_role("admin")
def atualizar_serie(serie_id):
    serie = Series.query.get_or_404(serie_id)
    dados = request.get_json() or {}
    if "nome" in dados and dados["nome"]:
        serie.nome = dados["nome"].strip()
    if "descricao" in dados:
        serie.descricao = dados["descricao"]
    if "categoria" in dados:
        serie.categoria = dados["categoria"]
    db.session.commit()
    return jsonify(serie.to_dict())

@app.route("/api/series/<int:serie_id>", methods=["DELETE"])
@require_role("admin")
def deletar_serie(serie_id):
    serie = Series.query.get_or_404(serie_id)
    db.session.delete(serie)
    db.session.commit()
    return "", 204

# ============================================
# ROTAS DE VÍDEOS
# ============================================

@app.route("/api/videos", methods=["GET"])
def listar_videos():
    categoria = request.args.get("categoria")
    serie_id = request.args.get("serie_id", type=int)
    query = Video.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    if serie_id:
        query = query.filter_by(serie_id=serie_id)
    videos = query.order_by(Video.id.desc()).all()
    return jsonify([v.to_dict() for v in videos])

@app.route("/api/videos/<int:video_id>", methods=["GET"])
def buscar_video(video_id):
    video = Video.query.get_or_404(video_id)
    return jsonify(video.to_dict())

@app.route("/api/videos", methods=["POST"])
@require_role("admin")
def criar_video():
    dados = request.get_json() or {}
    yt_id = extrair_yt_id(dados.get("yt_id", ""))
    if not yt_id:
        return jsonify({"erro": "URL ou ID do YouTube inválido"}), 400

    titulo = (dados.get("titulo") or "").strip()
    if not validar_entrada_texto(titulo, 200) or not titulo:
        return jsonify({"erro": "Título inválido"}), 400

    categoria = dados.get("categoria", "outros")
    if categoria not in VALID_CATEGORIES:
        return jsonify({"erro": "Categoria inválida"}), 400

    serie_id = dados.get("serie_id")
    if serie_id and not Series.query.get(serie_id):
        return jsonify({"erro": "Série não encontrada"}), 400

    if Video.query.filter_by(yt_id=yt_id).first():
        return jsonify({"erro": "Vídeo já cadastrado"}), 400

    # Validar campos opcionais
    descricao = dados.get("descricao", "")
    if not validar_entrada_texto(descricao, 5000, allow_empty=True):
        return jsonify({"erro": "Descrição inválida"}), 400
    
    ano = dados.get("ano", "")
    if not validar_entrada_texto(ano, 10, allow_empty=True):
        return jsonify({"erro": "Ano inválido"}), 400
    
    duracao = dados.get("duracao", "")
    if not validar_entrada_texto(duracao, 30, allow_empty=True):
        return jsonify({"erro": "Duração inválida"}), 400
    
    thumb = dados.get("thumb", "")
    if not validar_entrada_texto(thumb, 500, allow_empty=True):
        return jsonify({"erro": "Thumbnail inválida"}), 400
    
    temporada = dados.get("temporada", "")
    if not validar_entrada_texto(temporada, 30, allow_empty=True):
        return jsonify({"erro": "Temporada inválida"}), 400
    
    episodio = dados.get("episodio", "")
    if not validar_entrada_texto(episodio, 30, allow_empty=True):
        return jsonify({"erro": "Episódio inválido"}), 400

    video = Video(
        yt_id=yt_id,
        titulo=titulo,
        descricao=descricao,
        categoria=categoria,
        ano=ano,
        duracao=duracao,
        thumb=thumb,
        serie_id=serie_id,
        temporada=temporada,
        episodio=
