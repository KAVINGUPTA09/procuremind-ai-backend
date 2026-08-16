from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =========================================================
# DATABASE
# =========================================================

from app.database.database import Base, engine
from app.database import models

# =========================================================
# REDIS
# =========================================================

from app.services.redis_service import check_redis_connection

# =========================================================
# ROUTERS
# =========================================================

from app.api.routes import router as procurement_router
from app.api.auth_routes import router as auth_router
from app.api.history_routes import router as history_router
from app.api.report_routes import router as report_router


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="ProcureMind",
    version="1.0.0",
    description=(
        "ProcureMind is an AI-powered procurement platform "
        "that helps businesses make smarter purchasing decisions."
    )
)


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",

        "http://localhost:8081",
        "http://127.0.0.1:8081",

        "http://localhost:8082",
        "http://127.0.0.1:8082",

        "http://localhost:8083",
        "http://127.0.0.1:8083",

        "https://procurewise-insight.onrender.com",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(procurement_router)
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(report_router)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Welcome to ProcureMind AI",
        "documents": "/docs"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =========================================================
# REDIS HEALTH
# =========================================================

@app.get("/health/redis")
def redis_health():
    return {
        "redis_connected": check_redis_connection()
    }