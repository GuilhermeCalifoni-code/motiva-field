# API local — Motiva Field

```bash
cd api
copy .env.example .env
# preencha GEMINI_API_KEY em .env
uv run --with fastapi --with "uvicorn[standard]" --with python-multipart --with pydantic-settings --with google-genai uvicorn app.main:app --reload --port 8000
```

- Saúde: `GET http://127.0.0.1:8000/api/health`
- Análise: `POST http://127.0.0.1:8000/api/analises` com campo multipart `imagem`.
- Sem chave ou internet, o fallback só opera se `ALLOW_DEMO_FALLBACK=true` e é identificado explicitamente como `demo_local`.
