import csv
import os
import re
from argparse import ArgumentParser

from flask import Flask
from yt_dlp import YoutubeDL

from database import db, Series, Video


def limpar_nome(nome):
    return re.sub(r'[\\/*?:"<>|]', "", nome)


def montar_url(entrada):
    entrada = entrada.strip()
    if "youtube.com" in entrada or "youtu.be" in entrada:
        return entrada
    return f"https://www.youtube.com/playlist?list={entrada}"


def extract_playlist_entries(url):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info or "entries" not in info:
                return None

            links = []
            for entry in info["entries"]:
                if not entry:
                    continue
                video_id = entry.get("id")
                titulo = entry.get("title", "sem_titulo")
                if video_id:
                    links.append({"titulo": titulo, "link": f"https://www.youtube.com/watch?v={video_id}"})

            return links
    except Exception:
        return None


def save_entries(entries, formato="txt"):
    if not entries:
        print("Nenhum vídeo encontrado.")
        return

    nome = limpar_nome(entries[0].get("titulo", "playlist"))
    arquivo_saida = f"{nome}.{formato}"

    if formato == "csv":
        with open(arquivo_saida, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Titulo", "Link"])
            writer.writerows([[item["titulo"], item["link"]] for item in entries])
    else:
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            for item in entries:
                f.write(f"{item['titulo']} | {item['link']}\n")

    print(f"{len(entries)} vídeos salvos em: {arquivo_saida}")


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///streamflix.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app


def ensure_serie(nome, categoria="series", descricao=""):
    serie = Series.query.filter_by(nome=nome.strip()).first()
    if serie:
        return serie

    serie = Series(nome=nome.strip(), categoria=categoria, descricao=descricao)
    db.session.add(serie)
    db.session.commit()
    return serie


def import_playlist_to_db(entries, categoria="series", serie_name=None, serie_id=None, temporada="", episodio_inicio=None):
    if serie_id:
        serie = Series.query.get(serie_id)
        if not serie:
            raise ValueError("Série não encontrada")
    elif serie_name:
        serie = ensure_serie(serie_name, categoria)
    else:
        serie = None

    imported_videos = []
    for idx, item in enumerate(entries, start=1):
        yt_id = extrair_yt_id(item["link"])
        if not yt_id or Video.query.filter_by(yt_id=yt_id).first():
            continue

        episodio = ""
        if episodio_inicio is not None:
            try:
                episodio = str(int(episodio_inicio) + idx - 1)
            except ValueError:
                episodio = ""

        video = Video(
            yt_id=yt_id,
            titulo=item["titulo"],
            descricao="",
            categoria=categoria,
            ano="",
            duracao="",
            thumb="",
            serie_id=serie.id if serie else None,
            temporada=temporada,
            episodio=episodio,
        )
        db.session.add(video)
        imported_videos.append(video)

    db.session.commit()
    return imported_videos


def extrair_yt_id(valor):
    valor = (valor or "").strip()
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})", valor)
    if m:
        return m.group(1)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", valor):
        return valor
    return None


if __name__ == "__main__":
    parser = ArgumentParser(description="Extrator e importador de playlists para o banco de dados")
    parser.add_argument("playlist", help="Link ou ID da playlist do YouTube")
    parser.add_argument("--formato", choices=["txt", "csv"], default="txt")
    parser.add_argument("--importar", action="store_true", help="Importar vídeos para o banco")
    parser.add_argument("--categoria", default="series", help="Categoria dos vídeos")
    parser.add_argument("--serie", help="Nome da série a criar ou usar")
    parser.add_argument("--serie-id", type=int, help="ID da série existente")
    parser.add_argument("--temporada", default="", help="Temporada atribuída aos vídeos")
    parser.add_argument("--episodio-inicio", type=int, help="Número do primeiro episódio")
    args = parser.parse_args()

    playlist_url = montar_url(args.playlist)
    entries = extract_playlist_entries(playlist_url)
    if not entries:
        print("Falha ao extrair playlist.")
        raise SystemExit(1)

    if args.importar:
        app = create_app()
        with app.app_context():
            imported = import_playlist_to_db(
                entries,
                categoria=args.categoria,
                serie_name=args.serie,
                serie_id=args.serie_id,
                temporada=args.temporada,
                episodio_inicio=args.episodio_inicio,
            )
        print(f"{len(imported)} vídeos importados para o banco de dados.")
    else:
        save_entries(entries, args.formato)
