import unicodedata
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _normalize(s: str) -> str:
    """Quita tildes y pasa a lowercase para comparación accent-insensitive."""
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii').lower()

from app.database import get_db
from app.models import Cliente
from app.schemas import ClienteConVehiculos, ClienteCreate, ClienteOut, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=List[ClienteOut])
def list_clientes(
    q: Optional[str] = Query(None, description="Partial match on nombre or apellido"),
    db: Session = Depends(get_db),
):
    """List all clientes, optionally filtered by partial name/apellido."""
    query = db.query(Cliente)
    if q:
        like = f"%{q}%"
        query = query.filter(
            Cliente.nombre.ilike(like) | Cliente.apellido.ilike(like)
        )
    return query.all()


@router.post("", response_model=ClienteOut, status_code=201)
def create_cliente(data: ClienteCreate, db: Session = Depends(get_db)):
    """Create a new cliente."""
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    try:
        db.commit()
        db.refresh(cliente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El nif_dni ya está en uso.")
    return cliente


# IMPORTANT: /buscar must be defined BEFORE /{id} so FastAPI matches it first.
@router.get("/buscar", response_model=List[ClienteOut])
def buscar_clientes(
    apellido: Optional[str] = Query(None),
    nif_dni: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Search clientes by apellido (partial, case-insensitive) OR nif_dni (exact).
    If both are provided, apellido takes precedence.
    """
    if apellido is not None:
        # Filtrado en Python con normalización: quita tildes en query Y en apellido almacenado
        # Permite "martinez" → "Martínez", "garcia" → "García", etc.
        normalized_q = _normalize(apellido)
        all_clientes = db.query(Cliente).all()
        return [c for c in all_clientes if normalized_q in _normalize(c.apellido or '')]
    if nif_dni is not None:
        # Prefix-match: "18650000" encuentra "18650000Z"
        return db.query(Cliente).filter(Cliente.nif_dni.ilike(f"{nif_dni}%")).all()
    raise HTTPException(status_code=400, detail="Se requiere apellido o nif_dni")


@router.get("/{id}", response_model=ClienteConVehiculos)
def get_cliente(id: int, db: Session = Depends(get_db)):
    """Get a single cliente with their vehicles list."""
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    return cliente


@router.put("/{id}", response_model=ClienteOut)
def update_cliente(id: int, data: ClienteUpdate, db: Session = Depends(get_db)):
    """Update only the provided fields of a cliente."""
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(cliente, field, value)
    try:
        db.commit()
        db.refresh(cliente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El nif_dni ya está en uso.")
    return cliente
