from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import BudgetItem, Order
from app.state_machine import TERMINAL_STATES


def generate_numero_orden(db: Session) -> str:
    """
    Generate next order number in format YYYY-NNN.
    Count existing orders for current year and increment.
    Example: if there are 5 orders in 2026, returns "2026-006".
    """
    current_year = datetime.now(timezone.utc).year
    year_prefix = f"{current_year}-"

    count = (
        db.query(Order)
        .filter(Order.numero_orden.like(f"{year_prefix}%"))
        .count()
    )

    next_number = count + 1
    return f"{current_year}-{next_number:03d}"


def get_active_order_for_vehicle(db: Session, vehicle_id: int):
    """
    Return the active Order for a vehicle, or None.
    Active = estado NOT IN ("entregado", "rechazado").
    """
    return (
        db.query(Order)
        .filter(
            Order.vehicle_id == vehicle_id,
            Order.estado.notin_(TERMINAL_STATES),
        )
        .first()
    )


def apply_rejection_side_effects(
    db: Session, order: Order, config: dict[str, str]
) -> None:
    """
    Apply side effects when transitioning to "rechazado".

    Rules:
    - From "recibida": no action (no charge)
    - From "presupuestado": auto-create ONE BudgetItem with:
        concepto = "Cargo por diagnóstico"
        tipo = "mano_obra"
        cantidad = 0.5
        precio_unitario = float(config.get("tarifa_hora", "0"))
        es_cargo_cancelacion = True
    - From "en_reparacion": no action (mechanic manually adds items via
        CancellationDialog before this call)

    The `order` param is the SQLAlchemy Order instance (has .estado attribute).
    The `config` param is a dict of Config key→value (already fetched by the caller).
    After creating items, add them to `db` but do NOT commit — the caller commits.
    """
    if order.estado == "presupuestado":
        tarifa = float(config.get("tarifa_hora", "0"))
        item = BudgetItem(
            order_id=order.id,
            concepto="Cargo por diagnóstico",
            tipo="mano_obra",
            cantidad=0.5,
            precio_unitario=tarifa,
            es_cargo_cancelacion=True,
        )
        db.add(item)
    # "recibida" and "en_reparacion" → no automatic items created here
