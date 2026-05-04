# StreamFlix — Flask + SQLite

## Estrutura

```
streamflix/
├── main.py        # Servidor Flask + rotas da API
├── database.py    # Modelo do banco de dados
├── requirements.txt
└── static/
    └── index.html
```

## Rodando

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Iniciar o servidor
```bash
python main.py
```

Acesse: http://localhost:5000

## Rotas da API

| Método | Rota                    | Descrição              |
|--------|-------------------------|------------------------|
| GET    | /api/videos             | Lista todos os vídeos  |
| GET    | /api/videos?categoria=X | Filtra por categoria   |
| POST   | /api/videos             | Adiciona um vídeo      |
| PUT    | /api/videos/{id}        | Atualiza um vídeo      |
| DELETE | /api/videos/{id}        | Remove um vídeo        |
| GET    | /api/categorias         | Lista categorias       |

## Exemplo de POST
```json
{
  "yt_id": "https://youtu.be/dQw4w9WgXcQ",
  "titulo": "Never Gonna Give You Up",
  "categoria": "outros",
  "ano": "1987",
  "duracao": "3min"
}
```
