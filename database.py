from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Video(db.Model):
    __tablename__ = "videos"

    id        = db.Column(db.Integer, primary_key=True)
    yt_id     = db.Column(db.String(20), nullable=False)
    titulo    = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, default="")
    categoria = db.Column(db.String(50), default="outros")
    ano       = db.Column(db.String(10), default="")
    duracao   = db.Column(db.String(30), default="")
    thumb     = db.Column(db.Text, default="")

    def to_dict(self):
        return {
            "id":        self.id,
            "yt_id":     self.yt_id,
            "titulo":    self.titulo,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "ano":       self.ano,
            "duracao":   self.duracao,
            "thumb":     self.thumb,
        }
