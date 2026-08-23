# Lea$e — Phase 1 POC

POC funcional de financiamiento de maquinaria (FastAPI + React). El README general del
repositorio — con el modelo de dominio, el happy path completo, cómo ejecutar y probar, la
cobertura de requisitos y los límites conocidos de la POC — vive en
[`../../README.md`](../../README.md).

Resumen rápido:

```powershell
cd backend && uv sync && uv run uvicorn main:app --reload      # terminal 1
cd frontend && npm install && npm run dev                       # terminal 2
```

SPA en <http://127.0.0.1:5173>, Swagger en <http://127.0.0.1:8000/docs>. Identidades demo:
César (`CLIENT`), Juan Pedro (`LEASING`), Maxim (`BROKER`) — seleccionables desde
`POST /api/demo/session`.

