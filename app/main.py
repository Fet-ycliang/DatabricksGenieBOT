from fastapi import FastAPI
from app.core.config import DefaultConfig
from app.api.bot import router as bot_router
from app.api.genie import router as genie_router
from app.api.health import router as health_router

app = FastAPI(
    title="Databricks Genie Bot API",
    description="API for accessing Genie Service and Bot Framework integration.",
    version="1.0.0",
)

CONFIG = DefaultConfig()

# Include Routers
app.include_router(health_router, prefix="", tags=["health"])
app.include_router(bot_router, prefix="/api", tags=["bot"])
app.include_router(genie_router, prefix="/api/genie", tags=["genie"])

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Databricks Genie Bot",
        "docs": "/docs"
    }
