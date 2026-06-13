from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Config
from app.schemas import ConfigMap

router = APIRouter(prefix="/config", tags=["Config"])


@router.get("", response_model=ConfigMap)
def get_config(db: Session = Depends(get_db)):
    """Return all config key-value pairs as a dict."""
    rows = db.query(Config).all()
    return {row.clave: row.valor for row in rows}


@router.put("", response_model=ConfigMap)
def update_config(data: ConfigMap, db: Session = Depends(get_db)):
    """Upsert each key-value pair in the request body."""
    for clave, valor in data.root.items():
        existing = db.query(Config).filter(Config.clave == clave).first()
        if existing:
            existing.valor = valor
        else:
            db.add(Config(clave=clave, valor=valor))
    db.commit()
    # Return updated config
    rows = db.query(Config).all()
    return {row.clave: row.valor for row in rows}
