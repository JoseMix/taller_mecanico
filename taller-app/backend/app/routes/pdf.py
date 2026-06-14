from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from app.database import get_db
from app.models import Order, Vehicle, Config
from app.state_machine import TERMINAL_STATES

router = APIRouter(prefix="/ordenes", tags=["PDF"])

TEMPLATES_DIR = Path(__file__).parent.parent / "pdf_templates"

IVA_PORCENTAJE = 21


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )


@router.get("/{id}/pdf")
def download_pdf(id: int, db: Session = Depends(get_db)):
    """
    Generate and return a PDF invoice for a terminal-state order.

    - estado == "entregado"  → normal invoice using non-cancellation items
    - estado == "rechazado"  → cancellation invoice using cancellation items
    - Non-terminal orders    → 422
    """
    # 1. Fetch order with all relationships eagerly
    order = (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.vehicle).joinedload(Vehicle.cliente),
        )
        .filter(Order.id == id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada.")

    # 2. Only orders with a closed budget get invoices
    PDF_ALLOWED = TERMINAL_STATES | {"finalizada"}
    if order.estado not in PDF_ALLOWED:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Solo se puede generar factura para órdenes finalizadas o entregadas. "
                f"Estado actual: '{order.estado}'."
            ),
        )

    # 3. Determine invoice type and which items to include
    if order.estado in {"entregado", "finalizada"}:
        tipo_factura = "normal"
        relevant_items = [i for i in order.items if not i.es_cargo_cancelacion]
    else:  # rechazado
        tipo_factura = "cancelacion"
        relevant_items = [i for i in order.items if i.es_cargo_cancelacion]

    # 4. Get taller config from DB
    config_rows = db.query(Config).all()
    config = {row.clave: row.valor for row in config_rows}

    taller = {
        "nombre": config.get("nombre_taller", "Taller Mecánico"),
        "cif": config.get("cif_taller", ""),
        "direccion": config.get("direccion_taller", ""),
    }

    # 5. Build items list with subtotals and calculate totals
    items_ctx = []
    for item in relevant_items:
        subtotal = item.cantidad * item.precio_unitario
        items_ctx.append(
            {
                "concepto": item.concepto,
                "tipo": item.tipo,
                "cantidad": item.cantidad,
                "precio_unitario": item.precio_unitario,
                "subtotal": subtotal,
            }
        )

    base_imponible = sum(i["subtotal"] for i in items_ctx)
    iva_importe = round(base_imponible * IVA_PORCENTAJE / 100, 2)
    total = round(base_imponible + iva_importe, 2)

    # 6. Build template context
    vehicle = order.vehicle
    cliente = vehicle.cliente

    fecha_str = order.fecha_entrada.strftime("%d/%m/%Y")

    context = {
        "tipo_factura": tipo_factura,
        "taller": taller,
        "cliente": {
            "nombre": cliente.nombre,
            "apellido": cliente.apellido,
            "nif_dni": cliente.nif_dni,
            "direccion": f"{cliente.direccion}, {cliente.localidad} ({cliente.provincia})",
            "telefono": cliente.telefono,
        },
        "vehiculo": {
            "matricula": vehicle.matricula,
            "marca": vehicle.marca,
            "modelo": vehicle.modelo,
            "año": vehicle.año,
            "kilometraje": order.kilometraje,
        },
        "orden": {
            "numero_orden": order.numero_orden,
            "fecha": fecha_str,
        },
        "items": items_ctx,
        "base_imponible": base_imponible,
        "iva_porcentaje": IVA_PORCENTAJE,
        "iva_importe": iva_importe,
        "total": total,
    }

    # 7. Render Jinja2 template
    env = _get_jinja_env()
    template = env.get_template("factura.html")
    html_content = template.render(**context)

    # 8. Convert to PDF with WeasyPrint
    try:
        import weasyprint  # local import so missing system libs only fail at call time
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el PDF. Compruebe que WeasyPrint y sus dependencias del sistema están instalados. Detalle: {exc}",
        )

    # 9. Return PDF response
    filename = f"factura-{order.numero_orden}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
