from fastapi import FastAPI
from .database import init_db
from .routers import operators, sources, appeals

app = FastAPI(
    title="Mini-CRM Lead Distribution",
    description="Система распределения лидов между операторами по источникам",
    version="1.0.0"
)

# Инициализация БД при старте
@app.on_event("startup")
def on_startup():
    init_db()

# Подключение роутеров
app.include_router(operators.router)
app.include_router(sources.router)
app.include_router(appeals.router)


@app.get("/")
def root():
    return {
        "message": "Mini-CRM API",
        "docs": "/docs",
        "endpoints": {
            "operators": "/operators",
            "sources": "/sources",
            "appeals": "/appeals"
        }
    }