import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.core.api.routers import export, pbi, webhooks

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Plataforma BI - Studio Automation Core API",
    description="API para automação e extração de dados do Power BI Grupo Studio",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Origens permitidas para CORS (produção + dev local)
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "https://bi.grupostudio.tec.br,http://localhost:3000").split(",")

# CORS restrito aos domínios autorizados
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """
    Validação opcional de API Key via header X-API-Key.

    Só é aplicada quando a variável API_SECRET_KEY estiver definida no ambiente.
    Quando ausente, todos os requests passam (modo desenvolvimento).
    O endpoint /health é sempre acessível para health checks de infraestrutura.

    Para ativar em produção, adicione ao .env:
        API_SECRET_KEY=sua-chave-secreta-aqui
    """
    api_key = os.getenv("API_SECRET_KEY")

    # Chave não configurada — modo desenvolvimento, sem restrição
    if not api_key:
        return await call_next(request)

    # Health check sempre acessível (necessário para Docker/load balancer)
    if request.url.path == "/health":
        return await call_next(request)

    provided_key = request.headers.get("X-API-Key", "")
    if provided_key != api_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "API Key inválida ou ausente"},
        )

    return await call_next(request)


app.include_router(export.router, prefix="/api/v1/export", tags=["exportação"])
app.include_router(pbi.router, prefix="/api/v1/pbi", tags=["pbi"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
