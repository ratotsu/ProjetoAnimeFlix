from yt_dlp import YoutubeDL
import csv
import re

def limpar_nome(nome):
    # remove caracteres inválidos para arquivo
    return re.sub(r'[\\/*?:"<>|]', "", nome)

def montar_url(entrada):
    entrada = entrada.strip()
    if "youtube.com" in entrada:
        return entrada
    return f"https://www.youtube.com/playlist?list={entrada}"

def extrair_links_playlist(url, formato="txt"):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True
    }

    links = []

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info or "entries" not in info:
                print("Não foi possível ler a playlist.")
                return

            nome_playlist = limpar_nome(info.get("title", "playlist"))

            for entry in info["entries"]:
                if not entry:
                    continue

                video_id = entry.get("id")
                titulo = entry.get("title", "sem_titulo")

                if video_id:
                    link = f"https://www.youtube.com/watch?v={video_id}"
                    links.append((titulo, link))

    except Exception as e:
        print("Erro:", e)
        return

    if not links:
        print("Nenhum vídeo encontrado.")
        return

    arquivo_saida = f"{nome_playlist}.{formato}"

    if formato == "csv":
        with open(arquivo_saida, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Titulo", "Link"])
            writer.writerows(links)
    else:
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            for titulo, link in links:
                f.write(f"{titulo} | {link}\n")

    print(f"{len(links)} vídeos salvos em: {arquivo_saida}")


if __name__ == "__main__":
    print("=== Extrator de Playlist ===")

    entrada = input("Cole o LINK ou ID da playlist: ")
    url = montar_url(entrada)

    formato = input("Formato (txt/csv) [txt]: ").strip().lower()
    if formato not in ["txt", "csv"]:
        formato = "txt"

    extrair_links_playlist(url, formato)