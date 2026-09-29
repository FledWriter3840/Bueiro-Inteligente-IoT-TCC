# Painel Web Bueiro Inteligente

Frontend React/TypeScript que substitui o dashboard Streamlit. Reune visao geral, telemetria, eventos, analise e treinamento de IA, simulacao, insercao manual e mapa do inventario/chamados SAC.

## Requisitos

- Node.js 20.19+ ou 22.12+
- API FastAPI acessivel em `http://localhost:8000`
- MySQL e `DATABASE_URL` configurados para operacoes que consultam o banco

## Desenvolvimento

Na pasta `bueiro_inteligente_api/frontend`:

```powershell
npm install
npm run dev
```

Abra `http://localhost:5173`. O Vite encaminha chamadas `/api/*` para o FastAPI na porta 8000.

## Verificacoes

```powershell
npm run lint
npm run build
```
