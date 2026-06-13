import pytest
from fastapi import HTTPException

from app.state_machine import validate_transition


# ---------------------------------------------------------------------------
# 1. All 7 valid transitions pass without raising
# ---------------------------------------------------------------------------

class TestValidTransitions:
    @pytest.mark.parametrize("from_estado, to_estado", [
        ("recibida",      "presupuestado"),
        ("recibida",      "rechazado"),
        ("presupuestado", "en_reparacion"),
        ("presupuestado", "rechazado"),
        ("en_reparacion", "finalizada"),
        ("en_reparacion", "rechazado"),
        ("finalizada",    "entregado"),
    ])
    def test_valid_transition_does_not_raise(self, from_estado, to_estado):
        """All defined valid transitions should return None without raising."""
        result = validate_transition(from_estado, to_estado)
        assert result is None


# ---------------------------------------------------------------------------
# 2. Invalid transitions (skipping states / backwards)
# ---------------------------------------------------------------------------

class TestInvalidTransitions:
    @pytest.mark.parametrize("from_estado, to_estado", [
        ("recibida",      "finalizada"),   # skip states
        ("presupuestado", "entregado"),    # skip states
        ("en_reparacion", "recibida"),     # backwards
    ])
    def test_invalid_transition_raises_422(self, from_estado, to_estado):
        """Transitions that skip states or go backwards must raise HTTP 422."""
        with pytest.raises(HTTPException) as exc_info:
            validate_transition(from_estado, to_estado)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 3. Terminal states block all moves
# ---------------------------------------------------------------------------

class TestTerminalStates:
    @pytest.mark.parametrize("from_estado, to_estado", [
        ("entregado", "recibida"),
        ("entregado", "presupuestado"),
        ("rechazado", "recibida"),
        ("rechazado", "en_reparacion"),
    ])
    def test_terminal_state_raises_422(self, from_estado, to_estado):
        """Attempting to leave a terminal state must raise HTTP 422."""
        with pytest.raises(HTTPException) as exc_info:
            validate_transition(from_estado, to_estado)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 4. Unknown estado values
# ---------------------------------------------------------------------------

class TestUnknownEstados:
    def test_unknown_from_estado_raises_422(self):
        """An unrecognised from_estado must raise HTTP 422."""
        with pytest.raises(HTTPException) as exc_info:
            validate_transition("desconocido", "recibida")
        assert exc_info.value.status_code == 422

    def test_unknown_to_estado_raises_422(self):
        """An unrecognised to_estado must raise HTTP 422."""
        with pytest.raises(HTTPException) as exc_info:
            validate_transition("recibida", "desconocido")
        assert exc_info.value.status_code == 422
