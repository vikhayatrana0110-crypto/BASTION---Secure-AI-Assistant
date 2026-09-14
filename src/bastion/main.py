from fastapi import FastAPI


def create_app()-> FastAPI:
    app = FastAPI(title="Bastion")

    @app.get("/healthz")
    def healthz() -> dict[str,str]:
        return {"status": "ok"}
    return app  