from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pathlib import Path
from app.database import Base, engine
from app.routes import config, clientes, vehiculos, ordenes, items, pdf

SPEC_PATH = Path(__file__).parent.parent.parent.parent / "openapi" / "spec.yaml"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Taller Mecánico API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(clientes.router)
app.include_router(vehiculos.router)
app.include_router(ordenes.router)
app.include_router(items.router)
app.include_router(pdf.router)


@app.get("/openapi.yaml", include_in_schema=False)
def serve_openapi_yaml():
    return Response(SPEC_PATH.read_text(encoding="utf-8"), media_type="text/yaml")
