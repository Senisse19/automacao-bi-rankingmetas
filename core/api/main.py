from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.api.routers import export, webhooks

app = FastAPI(
    title="Plataforma BI - Studio Automation Core API",
    description="API para automação e extração de dados do Power BI Grupo Studio",
    version="1.0.0",
)

# Adicionando CORS para o frontend Next.js poder consultar as APIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desenvolvimento, restrito no futuro
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(export.router, prefix="/api/v1/export", tags=["exportação"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
