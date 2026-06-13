def test_get_config_returns_defaults(client):
    """GET /config returns the seeded default values."""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert data["tarifa_hora"] == "45"
    assert data["nombre_taller"] == "Taller Test"


def test_put_config_updates_value(client):
    """PUT /config updates tarifa_hora."""
    response = client.put("/config", json={"tarifa_hora": "60"})
    assert response.status_code == 200
    data = response.json()
    assert data["tarifa_hora"] == "60"


def test_get_after_put_reflects_change(client):
    """GET /config after PUT reflects the updated value."""
    client.put("/config", json={"tarifa_hora": "55"})
    response = client.get("/config")
    assert response.status_code == 200
    assert response.json()["tarifa_hora"] == "55"


def test_put_config_adds_new_key(client):
    """PUT /config can add a new key not previously in config."""
    response = client.put("/config", json={"nueva_clave": "nuevo_valor"})
    assert response.status_code == 200
    assert response.json()["nueva_clave"] == "nuevo_valor"
