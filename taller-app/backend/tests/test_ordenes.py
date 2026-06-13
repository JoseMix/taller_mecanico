"""
Tests for Ordenes CRUD endpoints:
  POST   /ordenes
  GET    /ordenes
  GET    /ordenes/{id}
  PUT    /ordenes/{id}
  DELETE /ordenes/{id}
"""

from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Shared test data / helpers
# ---------------------------------------------------------------------------

CLIENTE_BASE = {
    "nombre": "Ana",
    "apellido": "García",
    "nif_dni": "12345678A",
    "telefono": "600111222",
    "email": "ana@example.com",
    "direccion": "Calle Mayor 1",
    "localidad": "Madrid",
    "provincia": "Madrid",
}

VEHICLE_BASE = {
    "matricula": "5678XYZ",
    "marca": "Seat",
    "modelo": "León",
    "año": 2020,
}


def _create_cliente(client, overrides=None):
    """POST /clientes and return its JSON."""
    payload = {**CLIENTE_BASE, **(overrides or {})}
    resp = client.post("/clientes", json=payload)
    assert resp.status_code == 201, f"Failed to create cliente: {resp.json()}"
    return resp.json()


def _create_vehicle(client, cliente_id, overrides=None):
    """POST /vehiculos and return its JSON."""
    payload = {**VEHICLE_BASE, "cliente_id": cliente_id, **(overrides or {})}
    resp = client.post("/vehiculos", json=payload)
    assert resp.status_code == 201, f"Failed to create vehicle: {resp.json()}"
    return resp.json()


def _create_order(client, vehicle_id, overrides=None):
    """POST /ordenes and return the response object."""
    payload = {
        "vehicle_id": vehicle_id,
        "descripcion": "Revisión general",
        "kilometraje": 50000,
        **(overrides or {}),
    }
    return client.post("/ordenes", json=payload)


def _setup(client, cliente_overrides=None, vehicle_overrides=None):
    """Create a cliente and a vehicle, return (cliente, vehicle)."""
    cliente = _create_cliente(client, cliente_overrides)
    vehicle = _create_vehicle(client, cliente["id"], vehicle_overrides)
    return cliente, vehicle


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_order(client):
    """POST /ordenes creates order with estado=recibida and auto numero_orden."""
    _, vehicle = _setup(client)
    resp = _create_order(client, vehicle["id"])

    assert resp.status_code == 201, resp.json()
    data = resp.json()
    assert data["estado"] == "recibida"
    assert data["numero_orden"] is not None
    # numero_orden format: YYYY-NNN
    assert "-" in data["numero_orden"]
    assert data["vehicle_id"] == vehicle["id"]
    assert data["descripcion"] == "Revisión general"
    assert data["kilometraje"] == 50000
    assert "vehicle" in data
    assert "cliente" in data["vehicle"]
    assert isinstance(data["items"], list)


def test_create_order_vehicle_not_found(client):
    """POST /ordenes with unknown vehicle_id returns 404."""
    resp = _create_order(client, vehicle_id=99999)
    assert resp.status_code == 404


def test_create_duplicate_active_order_fails(client):
    """POST /ordenes when vehicle already has active order returns 422."""
    _, vehicle = _setup(client)
    # First order succeeds
    first = _create_order(client, vehicle["id"])
    assert first.status_code == 201

    # Second order for same vehicle → 422
    second = _create_order(client, vehicle["id"])
    assert second.status_code == 422
    assert "activa" in second.json()["detail"].lower()


def test_get_ordenes_kanban_list(client):
    """GET /ordenes returns non-terminal orders."""
    _, vehicle = _setup(client)
    order_resp = _create_order(client, vehicle["id"])
    assert order_resp.status_code == 201

    resp = client.get("/ordenes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    ids = [o["id"] for o in data]
    assert order_resp.json()["id"] in ids


def test_get_orden_by_id(client):
    """GET /ordenes/{id} returns full order with items and vehicle."""
    _, vehicle = _setup(client)
    order = _create_order(client, vehicle["id"]).json()

    resp = client.get(f"/ordenes/{order['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == order["id"]
    assert "items" in data
    assert "vehicle" in data
    assert "cliente" in data["vehicle"]


def test_get_orden_not_found(client):
    """GET /ordenes/{id} with unknown id returns 404."""
    resp = client.get("/ordenes/99999")
    assert resp.status_code == 404


def test_update_orden_editable_fields(client):
    """PUT /ordenes/{id} updates descripcion, kilometraje, notas_internas."""
    _, vehicle = _setup(client)
    order = _create_order(client, vehicle["id"]).json()

    update_payload = {
        "descripcion": "Cambio de aceite",
        "kilometraje": 75000,
        "notas_internas": "Cliente insiste en aceite sintético",
    }
    resp = client.put(f"/ordenes/{order['id']}", json=update_payload)
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["descripcion"] == "Cambio de aceite"
    assert data["kilometraje"] == 75000
    assert data["notas_internas"] == "Cliente insiste en aceite sintético"


def test_update_orden_not_found(client):
    """PUT /ordenes/{id} with unknown id returns 404."""
    resp = client.put("/ordenes/99999", json={"descripcion": "Nada"})
    assert resp.status_code == 404


def test_delete_orden_recibida(client):
    """DELETE /ordenes/{id} in recibida state returns 204."""
    _, vehicle = _setup(client)
    order = _create_order(client, vehicle["id"]).json()

    resp = client.delete(f"/ordenes/{order['id']}")
    assert resp.status_code == 204

    # Verify it's gone
    resp2 = client.get(f"/ordenes/{order['id']}")
    assert resp2.status_code == 404


def test_delete_orden_not_recibida_fails(client):
    """DELETE /ordenes/{id} when not in recibida returns 422."""
    _, vehicle = _setup(client)
    order = _create_order(client, vehicle["id"]).json()
    order_id = order["id"]

    # Manually advance estado via the DB (simulate being past recibida)
    # We patch using the db fixture indirectly via the PATCH estado endpoint
    # which doesn't exist yet (Task 13). Instead we manipulate directly via
    # a second client POST that bypasses — but the cleanest way is to reach
    # in through the SQLAlchemy session exposed by the client fixture.
    # Since we only have `client` here, we rely on the override_get_db session.
    # We'll use a workaround: update via the db that the client fixture uses.
    # The conftest exposes `db` as a separate fixture, so we pull it through
    # an extra fixture call. Since test functions can declare both fixtures:
    # This test is parameterised as `test_delete_orden_not_recibida_fails(client, db)`
    # — but we need to refactor to accept db too.  Instead, use the sqlalchemy
    # session from the app's dependency override.  We'll do it more simply by
    # directly updating the order through a raw API approach.
    #
    # Since PATCH /estado is Task 13 (not yet implemented), we access the db
    # directly. We rewrite this test to accept `db` fixture below (separate).
    pass


def test_delete_orden_not_recibida_fails_with_db(client, db):
    """DELETE /ordenes/{id} when not in recibida returns 422 (uses db to set state)."""
    from app.models import Order

    _, vehicle = _setup(client)
    order_resp = _create_order(client, vehicle["id"])
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    # Advance estado directly in the DB
    db_order = db.query(Order).filter(Order.id == order_id).first()
    db_order.estado = "presupuestado"
    db.commit()

    resp = client.delete(f"/ordenes/{order_id}")
    assert resp.status_code == 422
    assert "recibida" in resp.json()["detail"].lower()


def test_terminal_orders_in_last_7_days_appear_in_kanban(client, db):
    """GET /ordenes includes recently-terminal orders (last 7 days)."""
    from app.models import Order

    _, vehicle = _setup(client)
    order_resp = _create_order(client, vehicle["id"])
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    # Mark order as terminal (entregado) but within last 7 days
    db_order = db.query(Order).filter(Order.id == order_id).first()
    db_order.estado = "entregado"
    db_order.fecha_actualizacion = datetime.now(timezone.utc) - timedelta(days=3)
    db.commit()

    resp = client.get("/ordenes")
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert order_id in ids, "Recently-terminal order should appear in Kanban list"


def test_terminal_orders_older_than_7_days_excluded_from_kanban(client, db):
    """GET /ordenes excludes terminal orders older than 7 days."""
    from app.models import Order

    _, vehicle = _setup(client)
    order_resp = _create_order(client, vehicle["id"])
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    # Mark order as terminal (rechazado) and set fecha_actualizacion > 7 days ago
    db_order = db.query(Order).filter(Order.id == order_id).first()
    db_order.estado = "rechazado"
    db_order.fecha_actualizacion = datetime.now(timezone.utc) - timedelta(days=10)
    db.commit()

    resp = client.get("/ordenes")
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert order_id not in ids, "Old terminal order should be excluded from Kanban list"


def test_numero_orden_increments(client):
    """POST /ordenes assigns incrementing numero_orden within same year."""
    _, vehicle1 = _setup(
        client,
        cliente_overrides={"nif_dni": "11111111A", "apellido": "Uno"},
        vehicle_overrides={"matricula": "0001AAA"},
    )
    _, vehicle2 = _setup(
        client,
        cliente_overrides={"nif_dni": "22222222B", "apellido": "Dos"},
        vehicle_overrides={"matricula": "0002BBB"},
    )

    order1 = _create_order(client, vehicle1["id"]).json()
    order2 = _create_order(client, vehicle2["id"]).json()

    assert order1["numero_orden"] != order2["numero_orden"]
    # Both should share the same year prefix
    year = str(datetime.now(timezone.utc).year)
    assert order1["numero_orden"].startswith(year)
    assert order2["numero_orden"].startswith(year)
