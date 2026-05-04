# StreamFlix — Flask + Banco de Dados Organizado

## Estrutura

```
streamflix/
├── main.py            # Servidor Flask + rotas da API
├── database.py        # Modelos e organização do banco de dados
├── dlp_playlist.py    # Ferramenta de importação de playlists para o banco
├── requirements.txt
└── static/
    └── index.html
```

## Rodando

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar banco de dados

O sistema usa `DATABASE_URL` se estiver configurado. Caso contrário, ele ainda funciona em `sqlite:///streamflix.db`.

Exemplos:

- MySQL:
```bash
set DATABASE_URL=mysql+pymysql://usuario:senha@localhost/streamflix
```
- SQLite local:
```bash
set DATABASE_URL=sqlite:///streamflix.db
```

Você também pode criar a senha do root com:
```bash
set ROOT_PASSWORD=minhaSenhaSegura
```

### 3. Iniciar o servidor
```bash
python main.py
```

Acesse: http://localhost:5000

## Controle de acesso

- `usuario`: pode listar e assistir vídeos
- `admin`: pode listar, adicionar, editar e deletar vídeos e séries
- `root`: pode criar, editar e excluir usuários, além de todas as ações de admin

A autenticação é feita via `Authorization: Basic base64(usuario:senha)`.

## Rotas da API

| Método | Rota                            | Descrição |
|--------|----------------------------------|-----------|
| POST   | /api/auth/login                 | Verifica credenciais |
| GET    | /api/videos                     | Lista vídeos |
| GET    | /api/videos?categoria=X         | Filtra por categoria |
| GET    | /api/videos?serie_id=X          | Filtra por série |
| GET    | /api/videos/{id}                | Busca vídeo |
| POST   | /api/videos                     | Cria vídeo (admin) |
| PUT    | /api/videos/{id}                | Atualiza vídeo (admin) |
| DELETE | /api/videos/{id}                | Remove vídeo (admin) |
| GET    | /api/series                     | Lista séries |
| POST   | /api/series                     | Cria série (admin) |
| PUT    | /api/series/{id}                | Atualiza série (admin) |
| DELETE | /api/series/{id}               | Remove série (admin) |
| POST   | /api/playlists/import           | Importa playlist para o banco (admin) |
| GET    | /api/categorias                 | Lista categorias |
| GET    | /api/users                      | Lista usuários (root) |
| POST   | /api/users                      | Cria usuário (root) |

## Importar playlists para o banco

A ferramenta `dlp_playlist.py` agora pode importar vídeos diretamente para o banco de dados.

Exemplo:
```bash
python dlp_playlist.py https://www.youtube.com/playlist?list=PL... --importar --categoria series --serie "Minha Série" --temporada "1" --episodio-inicio 1
```
