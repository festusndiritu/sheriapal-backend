from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from app.db import create_db_and_tables
from app.routers import auth as auth_router
from app.routers import docs as docs_router
from app.routers import ai as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed)


app = FastAPI(lifespan=lifespan)


# include routers
app.include_router(auth_router.router)
app.include_router(docs_router.router)
app.include_router(ai_router.router)


# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: JSONResponse(
    status_code=429,
    content={"detail": "Rate limit exceeded. Max 100 requests per minute."}
))

# CORS
origins = [
    "https://sheriapal.vercel.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/health/ready")
def readiness_check():
    """Readiness check - verify database connection."""
    from app.db import engine
    try:
        with engine.begin() as conn:
            conn.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
