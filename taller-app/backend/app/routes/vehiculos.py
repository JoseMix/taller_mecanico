from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import BudgetItem, Cliente, Order, Vehicle
from app.schemas import VehicleConHistorial, VehicleCreate, VehicleOut

router = APIRouter(prefix="/vehiculos", tags=["Vehiculos"])


def _vehicle_with_history(db: Session, vehicle: Vehicle) -> Vehicle:
    """
    Eagerly load all nested relationships on a Vehicle instance
    so that Pydantic serialization (VehicleConHistorial) works without
    DetachedInstanceError.  Accesses are made inside the open session.
    """
    # Touch the relationships to force loading while session is open
    _ = vehicle.cliente
    for order in vehicle.ordenes:
        _ = order.items
        _ = order.vehicle
        _ = order.vehicle.cliente
    return vehicle


# IMPORTANT: /buscar must be defined BEFORE /{id} so FastAPI matches it first.
@router.get("/buscar", response_model=List[VehicleConHistorial])
def buscar_vehiculos(
    matricula: str = Query(..., description="Exact matricula to search for"),
    db: Session = Depends(get_db),
):
    """
    Search vehicles by matricula (exact match, case-insensitive).
    Returns empty list if not found.
    """
    vehicles = (
        db.query(Vehicle)
        .options(
            joinedload(Vehicle.cliente),
            joinedload(Vehicle.ordenes).joinedload(Order.items),
            joinedload(Vehicle.ordenes).joinedload(Order.vehicle).joinedload(Vehicle.cliente),
        )
        .filter(Vehicle.matricula.ilike(matricula))
        .all()
    )
    return vehicles


@router.get("/{id}", response_model=VehicleConHistorial)
def get_vehicle(id: int, db: Session = Depends(get_db)):
    """Get a vehicle by ID with its cliente and full order history."""
    vehicle = (
        db.query(Vehicle)
        .options(
            joinedload(Vehicle.cliente),
            joinedload(Vehicle.ordenes).joinedload(Order.items),
            joinedload(Vehicle.ordenes).joinedload(Order.vehicle).joinedload(Vehicle.cliente),
        )
        .filter(Vehicle.id == id)
        .first()
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado.")
    return vehicle


@router.post("", response_model=VehicleOut, status_code=201)
def create_vehicle(data: VehicleCreate, db: Session = Depends(get_db)):
    """Create a new vehicle linked to an existing cliente."""
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=404, detail="Cliente no encontrado."
        )

    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    try:
        db.commit()
        db.refresh(vehicle)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=422, detail="La matrícula ya está registrada."
        )
    return vehicle
