from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BudgetItem, Order
from app.schemas import BudgetItemCreate, BudgetItemOut, BudgetItemUpdate
from app.state_machine import LOCK_STATES

router = APIRouter(prefix="/ordenes", tags=["Items"])


def _get_order_or_404(db: Session, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")
    return order


def _get_item_or_404(db: Session, order_id: int, item_id: int) -> BudgetItem:
    item = (
        db.query(BudgetItem)
        .filter(BudgetItem.id == item_id, BudgetItem.order_id == order_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado.")
    return item


def _check_lock(order: Order, item: BudgetItem) -> None:
    """Raise 422 if a normal (non-cancellation) item is locked due to order state."""
    if not item.es_cargo_cancelacion and order.estado in LOCK_STATES:
        raise HTTPException(
            status_code=422,
            detail="Los items del presupuesto están bloqueados en este estado",
        )


@router.post("/{id}/items", response_model=BudgetItemOut, status_code=201)
def add_item(id: int, data: BudgetItemCreate, db: Session = Depends(get_db)):
    """Add a budget item to an order."""
    _get_order_or_404(db, id)

    item = BudgetItem(
        order_id=id,
        concepto=data.concepto,
        tipo=data.tipo,
        cantidad=data.cantidad,
        precio_unitario=data.precio_unitario,
        es_cargo_cancelacion=data.es_cargo_cancelacion,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{id}/items/{item_id}", response_model=BudgetItemOut)
def update_item(
    id: int,
    item_id: int,
    data: BudgetItemUpdate,
    db: Session = Depends(get_db),
):
    """Edit a budget item. Locked if order is in a lock state and item is not a cancellation charge."""
    order = _get_order_or_404(db, id)
    item = _get_item_or_404(db, id, item_id)
    _check_lock(order, item)

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{id}/items/{item_id}", status_code=204)
def delete_item(
    id: int,
    item_id: int,
    db: Session = Depends(get_db),
):
    """Delete a budget item. Locked if order is in a lock state and item is not a cancellation charge."""
    order = _get_order_or_404(db, id)
    item = _get_item_or_404(db, id, item_id)
    _check_lock(order, item)

    db.delete(item)
    db.commit()
    return Response(status_code=204)
