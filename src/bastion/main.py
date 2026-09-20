from contextlib import asynccontextmanager

from fastapi import FastAPI

from bastion.db import get_pool, verify_security_invariants


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_pool().connection() as conn:
        verify_security_invariants(conn)

    yield

def create_app()-> FastAPI:
    app = FastAPI(title="Bastion", lifespan=lifespan)

    @app.get("/healthz")
    def healthz() -> dict[str,str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        with get_pool().connection() as conn:
            conn.execute("select 1")

        return {"status": "ready"}
    
    return app  