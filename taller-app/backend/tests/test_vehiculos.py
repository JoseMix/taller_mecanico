"""
Tests for POST /vehiculos, GET /vehiculos/{id}, and GET /vehiculos/buscar endpoints.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CLIENTE_BASE = {
    "nombre": "Carlos",
    "apellido": "Rodríguez",
    "nif_dni": "87654321B",
    "telefono": "600000002",
    "email": "carlos@example.com",
    "direccion": "Avenida Central 5",
    "localidad": "Barcelona",
    "provincia": "Barcelona",
}

VEHICLE_BASE = {
    "matricula": "1234ABC",
    "marca": "Toyota",
    "modelo": "Corolla",
    "año": 2018,
}


def _create_cliente(client, overrides=None):
    """POST /clientes and return the response JSON."""
    payload = {**CLIENTE_BASE, **(overrides or {})}
    resp = client.post("/clientes", json=payload)
    assert resp.status_code == 201, f"Failed to create cliente: {resp.json()}"
    return resp.json()


def _create_vehicle(client, cliente_id, overrides=None):
    """POST /vehiculos and return the response JSON."""
    payload = {**VEHICLE_BASE, "cliente_id": cliente_id, **(overrides or {})}
    resp = client.post("/vehiculos", json=payload)
    return resp


def _create_order(client, vehicle_id):
    """POST /ordenes and return the response JSON."""
    payload = {
        "vehicle_id": vehicle_id,
        "descripcion": "Revisión general",
        "kilometraje": 50000,
    }
    resp = client.post("/ordenes", json=payload)
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_vehicle(client):
    """POST /vehiculos creates vehicle linked to existing cliente."""
    cliente = _create_cliente(client)
    resp = _create_vehicle(client, cliente["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["matricula"] == "1234ABC"
    assert data["marca"] == "Toyota"
    assert data["modelo"] == "Corolla"
    assert data["año"] == 2018
    assert data["cliente_id"] == cliente["id"]


def test_create_vehicle_cliente_not_found(client):
    """POST /vehiculos with unknown cliente_id returns 404."""
    resp = _create_vehicle(client, cliente_id=99999)
    assert resp.status_code == 404


def test_create_vehicle_duplicate_matricula_fails(client):
    """POST /vehiculos with duplicate matricula returns 422."""
    cliente = _create_cliente(client)
    _create_vehicle(client, cliente["id"])  # first succeeds

    # Same matricula, second cliente to rule out other constraints
    cliente2 = _create_cliente(client, {"nif_dni": "11111111C", "apellido": "Otro"})
    resp = _create_vehicle(client, cliente2["id"])  # same matricula
    assert resp.status_code == 422


def test_get_vehicle_by_id(client):
    """GET /vehiculos/{id} returns vehicle with cliente and ordenes."""
    cliente = _create_cliente(client)
    vehicle_resp = _create_vehicle(client, cliente["id"])
    vehicle_id = vehicle_resp.json()["id"]

    resp = client.get(f"/vehiculos/{vehicle_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == vehicle_id
    assert data["matricula"] == "1234ABC"
    assert "cliente" in data
    assert data["cliente"]["id"] == cliente["id"]
    assert "ordenes" in data
    assert isinstance(data["ordenes"], list)


def test_get_vehicle_not_found(client):
    """GET /vehiculos/{id} with unknown id returns 404."""
    resp = client.get("/vehiculos/99999")
    assert resp.status_code == 404


def test_search_by_matricula_found(client):
    """GET /vehiculos/buscar?matricula= returns matching vehicle."""
    cliente = _create_cliente(client)
    _create_vehicle(client, cliente["id"])

    resp = client.get("/vehiculos/buscar?matricula=1234ABC")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(v["matricula"] == "1234ABC" for v in data)


def test_search_by_matricula_not_found(client):
    """GET /vehiculos/buscar?matricula=XXXX returns empty list."""
    resp = client.get("/vehiculos/buscar?matricula=XXXXXX")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


def test_vehicle_order_history_included(client):
    """GET /vehiculos/{id} includes ordenes list (even if empty)."""
    cliente = _create_cliente(client)
    vehicle_resp = _create_vehicle(client, cliente["id"])
    vehicle_id = vehicle_resp.json()["id"]

    resp = client.get(f"/vehiculos/{vehicle_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "ordenes" in data
    # No orders created yet — list should be empty
    assert data["ordenes"] == []
