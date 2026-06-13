from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from app.crud import generate_numero_orden, get_active_order_for_vehicle
from app.database import get_db
from app.models import Order, Vehicle
from app.schemas import OrderCreate, OrderResumen, OrderUpdate
from app.state_machine import TERMINAL_STATES

router = APIRouter(prefix="/ordenes", tags=["Ordenes"])


def _load_order(db: Session, order_id: int) -> Order:
    """Fetch an order with items and vehicle.cliente eagerly loaded, or raise 404."""
    order = (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.vehicle).joinedload(Vehicle.cliente),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    return order


@router.post("", response_model=OrderResumen, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    """Create a new repair order for a vehicle."""
    # Check vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado.")

    # Check no active order already exists for this vehicle
    existing = get_active_order_for_vehicle(db, data.vehicle_id)
    if existing:
        raise HTTPException(
            status_code=422,
            detail=(
                f"El vehículo ya tiene una orden activa: {existing.numero_orden} "
                f"(estado: {existing.estado})."
            ),
        )

    numero_orden = generate_numero_orden(db)
    order = Order(
        numero_orden=numero_orden,
        vehicle_id=data.vehicle_id,
        descripcion=data.descripcion,
        kilometraje=data.kilometraje,
        notas_internas=data.notas_internas,
        estado="recibida",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return _load_order(db, order.id)


@router.get("", response_model=List[OrderResumen])
def list_ordenes(db: Session = Depends(get_db)):
    """
    Return orders for the Kanban board:
    - All non-terminal orders (estado not in entregado/rechazado)
    - Terminal orders updated within the last 7 days
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    orders = (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.vehicle).joinedload(Vehicle.cliente),
        )
        .filter(
            (Order.estado.notin_(TERMINAL_STATES))
            | (
                Order.estado.in_(TERMINAL_STATES)
                & (Order.fecha_actualizacion >= cutoff)
            )
        )
        .all()
    )
    return orders


@router.get("/{id}", response_model=OrderResumen)
def get_order(id: int, db: Session = Depends(get_db)):
    """Get full order detail including items and vehicle with cliente."""
    return _load_order(db, id)


@router.put("/{id}", response_model=OrderResumen)
def update_order(id: int, data: OrderUpdate, db: Session = Depends(get_db)):
    """Update editable fields of an order: descripcion, kilometraje, notas_internas."""
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    # Explicitly update fecha_actualizacion (onupdate may not fire without a real change)
    order.fecha_actualizacion = datetime.now(timezone.utc)

    db.commit()
    return _load_order(db, order.id)


@router.delete("/{id}", status_code=204)
def delete_order(id: int, db: Session = Depends(get_db)):
    """Delete an order only if its estado is 'recibida'."""
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")

    if order.estado != "recibida":
        raise HTTPException(
            status_code=422,
            detail=(
                f"Solo se pueden eliminar órdenes en estado 'recibida'. "
                f"Estado actual: '{order.estado}'."
            ),
        )

    db.delete(order)
    db.commit()
    return Response(status_code=204)
