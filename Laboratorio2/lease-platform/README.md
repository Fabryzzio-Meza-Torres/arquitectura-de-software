# Lea$e — Phase 1 POC

POC funcional de financiamiento de maquinaria. Implementa solicitud, expediente, negociación documentada, recepción de un resultado crediticio externo, simulación, firma, activación contractual y cronograma.

La plataforma **no** calcula crédito, negocia automáticamente, selecciona proveedores/equipos ni coordina compra, logística o entrega física. La recepción de maquinaria es sólo un estado del contrato.

## Ejecutar

Requisitos verificados: Python 3.13, Node 22, `uv` y npm.

Terminal 1:

```powershell
cd backend
uv sync
uv run uvicorn main:app --reload
```

Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

- SPA: <http://127.0.0.1:5173>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>

## Identidades demo

| ID | Usuario | Rol |
| --- | --- | --- |
| 1 | César | CLIENT |
| 2 | Juan Pedro | LEASING |
| 3 | Maxim | BROKER |
| 4 | Ana | LEASING, segunda atestación |

En Swagger, ejecute `POST /api/demo/session`, copie `access_token` y péguelo en **Authorize**. El callback externo usa `X-Integration-Key: poc-risk-secret`.

## Pruebas

```powershell
cd backend
uv run pytest

cd ../frontend
npm test
npx playwright install chromium
npm run test:e2e
npm run build
```

La prueba E2E recorre la API completa, abre la vista de César, ejecuta axe WCAG A/AA a 360 px y comprueba Swagger UI.

