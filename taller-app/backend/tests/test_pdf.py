"""
Tests for the PDF generation endpoint:
  GET /ordenes/{id}/pdf
"""
import pytest

from app.models import BudgetItem, Order

# ---------------------------------------------------------------------------
# Shared helpers (same pattern as other test modules)
# ---------------------------------------------------------------------------

CLIENTE_BASE = {
    "nombre": "Pedro",
    "apellido": "Martínez",
    "nif_dni": "PDF1234567",
    "telefono": "699000111",
    "email": "pedro@example.com",
    "direccion": "Calle PDF 1",
    "localidad": "Barcelona",
    "provincia": "Barcelona",
}

VEHICLE_BASE = {
    "matricula": "PDF0001X",
    "marca": "Toyota",
    "modelo": "Corolla",
    "año": 2021,
}


def _create_cliente(client, overrides=None):
    payload = {**CLIENTE_BASE, **(overrides or {})}
    resp = client.post("/clientes", json=payload)
    assert resp.status_code == 201, f"Failed to create cliente: {resp.json()}"
    return resp.json()


def _create_vehicle(client, cliente_id, overrides=None):
    payload = {**VEHICLE_BASE, "cliente_id": cliente_id, **(overrides or {})}
    resp = client.post("/vehiculos", json=payload)
    assert resp.status_code == 201, f"Failed to create vehicle: {resp.json()}"
    return resp.json()


def _create_order(client, vehicle_id, overrides=None):
    payload = {
        "vehicle_id": vehicle_id,
        "descripcion": "Revisión completa",
        "kilometraje": 75000,
        **(overrides or {}),
    }
    resp = client.post("/ordenes", json=payload)
    assert resp.status_code == 201, f"Failed to create order: {resp.json()}"
    return resp.json()


def _add_budget_item(db, order_id, concepto="Mano de obra", tipo="mano_obra",
                     cantidad=1.5, precio_unitario=45.0, es_cargo_cancelacion=False):
    """Insert a BudgetItem directly into the test DB."""
    item = BudgetItem(
        order_id=order_id,
        concepto=concepto,
        tipo=tipo,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        es_cargo_cancelacion=es_cargo_cancelacion,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _transition(client, order_id, nuevo_estado, items_cancelacion=None):
    """PATCH /ordenes/{id}/estado helper."""
    payload = {"nuevo_estado": nuevo_estado}
    if items_cancelacion is not None:
        payload["items_cancelacion"] = items_cancelacion
    return client.patch(f"/ordenes/{order_id}/estado", json=payload)


def _reach_entregado(client, db, order_id):
    """Drive an order from recibida all the way to entregado."""
    _transition(client, order_id, "presupuestado")
    _add_budget_item(db, order_id)
    _transition(client, order_id, "en_reparacion")
    _transition(client, order_id, "finalizada")
    resp = _transition(client, order_id, "entregado")
    assert resp.status_code == 200, f"Could not reach entregado: {resp.json()}"


def _reach_rechazado_from_presupuestado(client, db, order_id):
    """Drive an order from recibida to presupuestado, then reject (auto-charge created)."""
    _transition(client, order_id, "presupuestado")
    resp = _transition(client, order_id, "rechazado")
    assert resp.status_code == 200, f"Could not reach rechazado: {resp.json()}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pdf_for_entregado_order(client, db):
    """GET /ordenes/{id}/pdf on entregado order returns 200 with application/pdf."""
    cliente = _create_cliente(client, overrides={"nif_dni": "PDF1111111"})
    vehicle = _create_vehicle(client, cliente["id"], overrides={"matricula": "PDF001AA"})
    order = _create_order(client, vehicle["id"])
    order_id = order["id"]

    _reach_entregado(client, db, order_id)

    resp = client.get(f"/ordenes/{order_id}/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"


def test_pdf_for_rechazado_order(client, db):
    """GET /ordenes/{id}/pdf on rechazado order returns 200 with application/pdf."""
    cliente = _create_cliente(client, overrides={"nif_dni": "PDF2222222"})
    vehicle = _create_vehicle(client, cliente["id"], overrides={"matricula": "PDF002BB"})
    order = _create_order(client, vehicle["id"])
    order_id = order["id"]

    _reach_rechazado_from_presupuestado(client, db, order_id)

    resp = client.get(f"/ordenes/{order_id}/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"


def test_pdf_non_terminal_order_returns_422(client, db):
    """GET /ordenes/{id}/pdf on a non-terminal order returns 422."""
    cliente = _create_cliente(client, overrides={"nif_dni": "PDF3333333"})
    vehicle = _create_vehicle(client, cliente["id"], overrides={"matricula": "PDF003CC"})
    order = _create_order(client, vehicle["id"])
    order_id = order["id"]

    # Order is in 'recibida' — non-terminal
    resp = client.get(f"/ordenes/{order_id}/pdf")
    assert resp.status_code == 422

    # Also test presupuestado
    _transition(client, order_id, "presupuestado")
    resp = client.get(f"/ordenes/{order_id}/pdf")
    assert resp.status_code == 422


def test_pdf_filename_contains_numero_orden(client, db):
    """Content-Disposition header contains the numero_orden."""
    cliente = _create_cliente(client, overrides={"nif_dni": "PDF4444444"})
    vehicle = _create_vehicle(client, cliente["id"], overrides={"matricula": "PDF004DD"})
    order = _create_order(client, vehicle["id"])
    order_id = order["id"]
    numero_orden = order["numero_orden"]

    _reach_entregado(client, db, order_id)

    resp = client.get(f"/ordenes/{order_id}/pdf")
    assert resp.status_code == 200

    content_disposition = resp.headers.get("content-disposition", "")
    assert numero_orden in content_disposition, (
        f"Expected '{numero_orden}' in Content-Disposition, got: '{content_disposition}'"
    )


def test_pdf_not_found(client, db):
    """GET /ordenes/{id}/pdf with unknown id returns 404."""
    resp = client.get("/ordenes/99999/pdf")
    assert resp.status_code == 404


def test_pdf_entregado_uses_non_cancellation_items(client, db):
    """PDF for entregado order should use non-cancellation items."""
    cliente = _create_cliente(client, overrides={"nif_dni": "PDF5555555"})
    vehicle = _create_vehicle(client, cliente["id"], overrides={"matricula": "PDF005EE"})
    order = _create_order(client, vehicle["id"])
    order_id = order["id"]

    _reach_entregado(client, db, order_id)

    resp = client.get(f"/ordenes/{order_id}/pdf")
    assert resp.status_code == 200
    # The response is binary PDF; we verify it's non-empty and starts with PDF magic bytes
    assert len(resp.content) > 100
    assert resp.content[:4] == b"%PDF"


def test_pdf_rechazado_uses_cancellation_items(client, db):
    """PDF for rechazado order should use cancellation items (auto-charge created)."""
    cliente = _create_cliente(client, overrides={"nif_dni": "PDF6666666"})
    vehicle = _create_vehicle(client, cliente["id"], overrides={"matricula": "PDF006FF"})
    order = _create_order(client, vehicle["id"])
    order_id = order["id"]

    _reach_rechazado_from_presupuestado(client, db, order_id)

    resp = client.get(f"/ordenes/{order_id}/pdf")
    assert resp.status_code == 200
    assert len(resp.content) > 100
    assert resp.content[:4] == b"%PDF"
