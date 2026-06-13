import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import Config

# ---------------------------------------------------------------------------
# In-memory SQLite engine shared across the fixture pair
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite://"  # empty path = in-memory

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db():
    """
    In-memory SQLite engine, creates all tables, yields session, drops all after.
    Each test gets a clean database.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    FastAPI TestClient with get_db dependency overridden to use the test db session.
    Seeds default Config values before yielding the client.
    """
    # Seed default config values
    db.add(Config(clave="tarifa_hora", valor="45"))
    db.add(Config(clave="nombre_taller", valor="Taller Test"))
    db.add(Config(clave="cif_taller", valor="B12345678"))
    db.add(Config(clave="direccion_taller", valor="Calle Test 1"))
    db.commit()

    def override_get_db():
        yield db

    # Import app here so that if main.py doesn't exist yet, only the
    # `client` fixture fails — the `db` fixture (and tests that only use
    # `db`) remain functional.
    try:
        from app.main import app  # noqa: PLC0415
    except ImportError:
        pytest.skip("app/main.py not yet created (Task 16) — skipping client fixture")
        return

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
