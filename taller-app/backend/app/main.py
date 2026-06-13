from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes import config, clientes, vehiculos, ordenes, items

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
