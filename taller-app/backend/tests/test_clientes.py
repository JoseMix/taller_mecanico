"""
Tests for GET/POST/PUT /clientes and GET /clientes/buscar endpoints.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CLIENTE_BASE = {
    "nombre": "Juan",
    "apellido": "García",
    "nif_dni": "12345678A",
    "telefono": "600000001",
    "email": "juan@example.com",
    "direccion": "Calle Mayor 1",
    "localidad": "Madrid",
    "provincia": "Madrid",
}


def _create_cliente(client, overrides=None):
    """POST /clientes and return the response object."""
    payload = {**CLIENTE_BASE, **(overrides or {})}
    return client.post("/clientes", json=payload)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_cliente(client):
    """POST /clientes creates and returns cliente with id."""
    resp = _create_cliente(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["nombre"] == "Juan"
    assert data["apellido"] == "García"
    assert data["nif_dni"] == "12345678A"


def test_create_cliente_duplicate_nif_dni_fails(client):
    """POST /clientes with duplicate nif_dni returns 422 or 400."""
    _create_cliente(client)
    resp = _create_cliente(client)  # same nif_dni
    assert resp.status_code in (400, 422)


def test_get_cliente_by_id(client):
    """GET /clientes/{id} returns cliente with vehiculos list."""
    created = _create_cliente(client).json()
    cliente_id = created["id"]

    resp = client.get(f"/clientes/{cliente_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == cliente_id
    assert data["apellido"] == "García"
    assert "vehiculos" in data
    assert isinstance(data["vehiculos"], list)


def test_get_cliente_not_found(client):
    """GET /clientes/{id} with unknown id returns 404."""
    resp = client.get("/clientes/99999")
    assert resp.status_code == 404


def test_search_by_apellido_partial(client):
    """GET /clientes/buscar?apellido=arc finds 'García' and 'Marcos'."""
    _create_cliente(client, {"apellido": "García", "nif_dni": "11111111A"})
    _create_cliente(client, {"apellido": "Marcos", "nif_dni": "22222222B"})
    _create_cliente(client, {"apellido": "López", "nif_dni": "33333333C"})

    resp = client.get("/clientes/buscar?apellido=arc")
    assert resp.status_code == 200
    apellidos = [c["apellido"] for c in resp.json()]
    assert "García" in apellidos
    assert "Marcos" in apellidos
    assert "López" not in apellidos


def test_search_by_apellido_case_insensitive(client):
    """GET /clientes/buscar?apellido=GOMEZ (uppercase) finds 'Gomez' (lowercase)."""
    _create_cliente(client, {"apellido": "Gomez", "nif_dni": "11111111A"})

    resp = client.get("/clientes/buscar?apellido=GOMEZ")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(c["apellido"] == "Gomez" for c in data)


def test_search_by_nif_dni_exact(client):
    """GET /clientes/buscar?nif_dni=12345678A returns exact match only."""
    _create_cliente(client, {"nif_dni": "12345678A", "apellido": "García"})
    _create_cliente(client, {"nif_dni": "87654321B", "apellido": "López"})

    resp = client.get("/clientes/buscar?nif_dni=12345678A")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nif_dni"] == "12345678A"


def test_search_by_nif_dni_no_match(client):
    """GET /clientes/buscar?nif_dni=99999999X returns empty list."""
    resp = client.get("/clientes/buscar?nif_dni=99999999X")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_without_params_returns_400(client):
    """GET /clientes/buscar with no params returns 400."""
    resp = client.get("/clientes/buscar")
    assert resp.status_code == 400


def test_update_cliente(client):
    """PUT /clientes/{id} updates only provided fields."""
    created = _create_cliente(client).json()
    cliente_id = created["id"]

    resp = client.put(
        f"/clientes/{cliente_id}",
        json={"telefono": "699999999", "email": "nuevo@example.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["telefono"] == "699999999"
    assert data["email"] == "nuevo@example.com"
    # Fields not included in the update should remain unchanged
    assert data["nombre"] == created["nombre"]
    assert data["apellido"] == created["apellido"]
    assert data["nif_dni"] == created["nif_dni"]
