from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import db, Video
import os

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///streamflix.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()


# --- Frontend ---

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# --- Videos ---

@app.route("/api/videos", methods=["GET"])
def listar_videos():
    categoria = request.args.get("categoria")
    query = Video.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    videos = query.order_by(Video.id.desc()).all()
    return jsonify([v.to_dict() for v in videos])


@app.route("/api/videos/<int:video_id>", methods=["GET"])
def buscar_video(video_id):
    video = Video.query.get_or_404(video_id)
    return jsonify(video.to_dict())


@app.route("/api/videos", methods=["POST"])
def criar_video():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    yt_id = extrair_yt_id(dados.get("yt_id", ""))
    if not yt_id:
        return jsonify({"erro": "URL ou ID do YouTube inválido"}), 400

    titulo = dados.get("titulo", "").strip()
    if not titulo:
        return jsonify({"erro": "Título obrigatório"}), 400

    categoria = dados.get("categoria", "outros")
    if categoria not in ("filmes", "series", "docs", "outros"):
        return jsonify({"erro": "Categoria inválida"}), 400

    video = Video(
        yt_id=yt_id,
        titulo=titulo,
        descricao=dados.get("descricao", ""),
        categoria=categoria,
        ano=dados.get("ano", ""),
        duracao=dados.get("duracao", ""),
        thumb=dados.get("thumb", ""),
    )
    db.session.add(video)
    db.session.commit()
    return jsonify(video.to_dict()), 201


@app.route("/api/videos/<int:video_id>", methods=["PUT"])
def atualizar_video(video_id):
    video = Video.query.get_or_404(video_id)
    dados = request.get_json()
    campos = ("titulo", "descricao", "categoria", "ano", "duracao", "thumb")
    for campo in campos:
        if campo in dados:
            setattr(video, campo, dados[campo])
    db.session.commit()
    return jsonify(video.to_dict())


@app.route("/api/videos/<int:video_id>", methods=["DELETE"])
def deletar_video(video_id):
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    return "", 204


@app.route("/api/categorias", methods=["GET"])
def listar_categorias():
    cats = db.session.query(Video.categoria).distinct().all()
    return jsonify([c[0] for c in cats])


# --- Utilitário ---

def extrair_yt_id(valor):
    import re
    valor = valor.strip()
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})", valor)
    if m:
        return m.group(1)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", valor):
        return valor
    return None


if __name__ == "__main__":
    app.run(debug=True)
