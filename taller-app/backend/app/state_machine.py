from fastapi import HTTPException

TERMINAL_STATES = {"entregado", "rechazado"}
LOCK_STATES = {"en_reparacion", "finalizada", "entregado", "rechazado"}

TRANSITIONS: dict[str, list[str]] = {
    "recibida":      ["presupuestado", "rechazado"],
    "presupuestado": ["en_reparacion", "rechazado"],
    "en_reparacion": ["finalizada", "rechazado"],
    "finalizada":    ["entregado"],
    "entregado":     [],
    "rechazado":     [],
}


def validate_transition(from_estado: str, to_estado: str) -> None:
    """Raises HTTPException(422) if the transition is not allowed."""
    if from_estado not in TRANSITIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Estado desconocido: '{from_estado}'. "
                   f"Los estados válidos son: {sorted(TRANSITIONS.keys())}.",
        )
    if to_estado not in TRANSITIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Estado destino desconocido: '{to_estado}'. "
                   f"Los estados válidos son: {sorted(TRANSITIONS.keys())}.",
        )
    allowed = TRANSITIONS[from_estado]
    if to_estado not in allowed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Transición no permitida: '{from_estado}' → '{to_estado}'. "
                f"Desde '{from_estado}' se puede ir a: {allowed or '(ninguno — estado terminal)'}."
            ),
        )
