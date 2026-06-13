"""
Tests for Items endpoints:
  POST   /ordenes/{id}/items
  PUT    /ordenes/{id}/items/{item_id}
  DELETE /ordenes/{id}/items/{item_id}
"""

from app.models import BudgetItem, Order, Vehicle, Cliente

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

CLIENTE_BASE = {
    "nombre": "Luis",
    "apellido": "Fernandez",
    "nif_dni": "99887766Z",
    "telefono": "611222333",
    "email": "luis@example.com",
    "direccion": "Avenida Test 5",
    "localidad": "Valencia",
    "provincia": "Valencia",
}

VEHICLE_BASE = {
    "matricula": "9988TTZ",
    "marca": "Ford",
    "modelo": "Focus",
    "año": 2019,
}

ITEM_BASE = {
    "concepto": "Cambio de aceite",
    "tipo": "mano_obra",
    "cantidad": 1.0,
    "precio_unitario": 45.0,
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


def _create_order(client, vehicle_id):
    payload = {
        "vehicle_id": vehicle_id,
        "descripcion": "Revisión general",
        "kilometraje": 30000,
    }
    resp = client.post("/ordenes", json=payload)
    assert resp.status_code == 201, f"Failed to create order: {resp.json()}"
    return resp.json()


def _setup(client, cliente_overrides=None, vehicle_overrides=None):
    """Create a cliente, a vehicle, and an order. Return order dict."""
    cliente = _create_cliente(client, cliente_overrides)
    vehicle = _create_vehicle(client, cliente["id"], vehicle_overrides)
    order = _create_order(client, vehicle["id"])
    return order


def _add_budget_item_db(db, order_id, concepto="Mano de obra", tipo="mano_obra",
                        cantidad=1, precio_unitario=45, es_cargo_cancelacion=False):
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


def _set_order_estado(db, order_id, estado):
    """Directly set an order's estado in the DB."""
    order = db.query(Order).filter(Order.id == order_id).first()
    order.estado = estado
    db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_add_item_to_order(client):
    """POST /ordenes/{id}/items adds item and returns it."""
    order = _setup(client)
    order_id = order["id"]

    payload = {**ITEM_BASE, "es_cargo_cancelacion": False}
    resp = client.post(f"/ordenes/{order_id}/items", json=payload)

    assert resp.status_code == 201, resp.json()
    data = resp.json()
    assert data["order_id"] == order_id
    assert data["concepto"] == ITEM_BASE["concepto"]
    assert data["tipo"] == ITEM_BASE["tipo"]
    assert data["cantidad"] == ITEM_BASE["cantidad"]
    assert data["precio_unitario"] == ITEM_BASE["precio_unitario"]
    assert data["es_cargo_cancelacion"] is False
    assert "id" in data


def test_add_item_order_not_found(client):
    """POST /ordenes/{id}/items with unknown order returns 404."""
    payload = {**ITEM_BASE, "es_cargo_cancelacion": False}
    resp = client.post("/ordenes/99999/items", json=payload)
    assert resp.status_code == 404


def test_edit_item_in_recibida_state(client, db):
    """PUT /ordenes/{id}/items/{item_id} works in recibida state."""
    order = _setup(client)
    order_id = order["id"]

    # Add item via API to get its id
    payload = {**ITEM_BASE, "es_cargo_cancelacion": False}
    add_resp = client.post(f"/ordenes/{order_id}/items", json=payload)
    assert add_resp.status_code == 201
    item_id = add_resp.json()["id"]

    # Update the item — order is still in 'recibida'
    update_payload = {"concepto": "Cambio de filtro", "precio_unitario": 30.0}
    resp = client.put(f"/ordenes/{order_id}/items/{item_id}", json=update_payload)

    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["concepto"] == "Cambio de filtro"
    assert data["precio_unitario"] == 30.0
    # Other fields unchanged
    assert data["tipo"] == ITEM_BASE["tipo"]


def test_edit_item_in_locked_state_fails(client, db):
    """PUT on a non-cancellation item when order is in en_reparacion returns 422."""
    order = _setup(
        client,
        cliente_overrides={"nif_dni": "LK111111L"},
        vehicle_overrides={"matricula": "LK0001AA"},
    )
    order_id = order["id"]

    # Add a normal budget item via DB
    item = _add_budget_item_db(db, order_id, es_cargo_cancelacion=False)

    # Move order to a locked state
    _set_order_estado(db, order_id, "en_reparacion")

    # Attempt to edit the item — should be rejected
    resp = client.put(
        f"/ordenes/{order_id}/items/{item.id}",
        json={"concepto": "Intento bloqueado"},
    )
    assert resp.status_code == 422
    assert "bloqueados" in resp.json()["detail"].lower()


def test_edit_cancellation_item_in_locked_state_allowed(client, db):
    """PUT on a cancellation item (es_cargo_cancelacion=True) is allowed even in locked state."""
    order = _setup(
        client,
        cliente_overrides={"nif_dni": "CA222222C"},
        vehicle_overrides={"matricula": "CA0002BB"},
    )
    order_id = order["id"]

    # Add a cancellation budget item via DB
    item = _add_budget_item_db(db, order_id, es_cargo_cancelacion=True)

    # Move order to a locked state
    _set_order_estado(db, order_id, "en_reparacion")

    # Editing a cancellation item should be allowed
    resp = client.put(
        f"/ordenes/{order_id}/items/{item.id}",
        json={"concepto": "Cargo ajustado", "precio_unitario": 22.5},
    )
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["concepto"] == "Cargo ajustado"
    assert data["precio_unitario"] == 22.5
    assert data["es_cargo_cancelacion"] is True


def test_delete_item_in_recibida_state(client, db):
    """DELETE /ordenes/{id}/items/{item_id} works in recibida state."""
    order = _setup(
        client,
        cliente_overrides={"nif_dni": "DE333333D"},
        vehicle_overrides={"matricula": "DE0003CC"},
    )
    order_id = order["id"]

    item = _add_budget_item_db(db, order_id, es_cargo_cancelacion=False)

    resp = client.delete(f"/ordenes/{order_id}/items/{item.id}")
    assert resp.status_code == 204

    # Confirm it no longer exists
    get_resp = client.get(f"/ordenes/{order_id}")
    assert get_resp.status_code == 200
    item_ids = [i["id"] for i in get_resp.json()["items"]]
    assert item.id not in item_ids


def test_delete_item_in_locked_state_fails(client, db):
    """DELETE on a non-cancellation item when order is locked returns 422."""
    order = _setup(
        client,
        cliente_overrides={"nif_dni": "DL444444D"},
        vehicle_overrides={"matricula": "DL0004DD"},
    )
    order_id = order["id"]

    item = _add_budget_item_db(db, order_id, es_cargo_cancelacion=False)

    # Move to a locked state
    _set_order_estado(db, order_id, "finalizada")

    resp = client.delete(f"/ordenes/{order_id}/items/{item.id}")
    assert resp.status_code == 422
    assert "bloqueados" in resp.json()["detail"].lower()


def test_item_not_found(client):
    """PUT/DELETE with unknown item_id returns 404."""
    order = _setup(
        client,
        cliente_overrides={"nif_dni": "NF555555N"},
        vehicle_overrides={"matricula": "NF0005EE"},
    )
    order_id = order["id"]

    put_resp = client.put(
        f"/ordenes/{order_id}/items/99999",
        json={"concepto": "No existe"},
    )
    assert put_resp.status_code == 404

    delete_resp = client.delete(f"/ordenes/{order_id}/items/99999")
    assert delete_resp.status_code == 404
