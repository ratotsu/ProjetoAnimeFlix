from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role          = db.Column(db.String(20), nullable=False, default="usuario")
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }


class Series(db.Model):
    __tablename__ = "series"

    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(200), unique=True, nullable=False)
    descricao   = db.Column(db.Text, default="")
    categoria   = db.Column(db.String(50), default="series")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    videos      = db.relationship("Video", back_populates="serie", cascade="all, delete-orphan")

    def to_dict(self, include_videos=False):
        data = {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "created_at": self.created_at.isoformat(),
        }
        if include_videos:
            data["videos"] = [video.to_dict(include_serie=False) for video in self.videos]
        return data


class Video(db.Model):
    __tablename__ = "videos"

    id          = db.Column(db.Integer, primary_key=True)
    yt_id       = db.Column(db.String(20), nullable=False)
    titulo      = db.Column(db.String(200), nullable=False)
    descricao   = db.Column(db.Text, default="")
    categoria   = db.Column(db.String(50), default="outros")
    ano         = db.Column(db.String(10), default="")
    duracao     = db.Column(db.String(30), default="")
    thumb       = db.Column(db.Text, default="")
    serie_id    = db.Column(db.Integer, db.ForeignKey("series.id"), nullable=True)
    temporada   = db.Column(db.String(30), default="")
    episodio    = db.Column(db.String(30), default="")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    serie       = db.relationship("Series", back_populates="videos")

    def to_dict(self, include_serie=False):
        data = {
            "id": self.id,
            "yt_id": self.yt_id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "ano": self.ano,
            "duracao": self.duracao,
            "thumb": self.thumb,
            "serie_id": self.serie_id,
            "temporada": self.temporada,
            "episodio": self.episodio,
            "created_at": self.created_at.isoformat(),
        }
        if include_serie and self.serie:
            data["serie"] = self.serie.to_dict(include_videos=False)
        return data
