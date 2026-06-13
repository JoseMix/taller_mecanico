from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, RootModel


# ---------------------------------------------------------------------------
# BudgetItem schemas
# ---------------------------------------------------------------------------

class BudgetItemBase(BaseModel):
    concepto: str
    tipo: str  # mano_obra | pieza
    cantidad: float
    precio_unitario: float
    es_cargo_cancelacion: bool = False


class BudgetItemCreate(BudgetItemBase):
    pass


class BudgetItemUpdate(BaseModel):
    concepto: Optional[str] = None
    tipo: Optional[str] = None
    cantidad: Optional[float] = None
    precio_unitario: Optional[float] = None
    es_cargo_cancelacion: Optional[bool] = None


class BudgetItemOut(BudgetItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Cliente schemas
# ---------------------------------------------------------------------------

class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    nif_dni: str
    telefono: str
    email: Optional[str] = None
    direccion: str
    localidad: str
    provincia: str


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    nif_dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None


class ClienteOut(ClienteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Vehicle schemas
# ---------------------------------------------------------------------------

class VehicleBase(BaseModel):
    cliente_id: int
    matricula: str
    marca: str
    modelo: str
    año: int


class VehicleCreate(VehicleBase):
    pass


class VehicleOut(VehicleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class VehicleConCliente(BaseModel):
    id: int
    matricula: str
    marca: str
    modelo: str
    año: int
    cliente: ClienteOut

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Order schemas — forward references resolved below
# ---------------------------------------------------------------------------

class OrderBase(BaseModel):
    vehicle_id: int
    descripcion: str
    kilometraje: Optional[int] = None
    notas_internas: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    descripcion: Optional[str] = None
    kilometraje: Optional[int] = None
    notas_internas: Optional[str] = None


class OrderResumen(BaseModel):
    id: int
    numero_orden: str
    vehicle_id: int
    estado: str
    descripcion: str
    kilometraje: Optional[int] = None
    notas_internas: Optional[str] = None
    fecha_entrada: datetime
    fecha_actualizacion: datetime
    fecha_entrega: Optional[datetime] = None
    items: List[BudgetItemOut] = []
    vehicle: VehicleConCliente

    model_config = ConfigDict(from_attributes=True)


class OrderOut(OrderResumen):
    pass


class EstadoTransition(BaseModel):
    nuevo_estado: str
    items_cancelacion: Optional[List[BudgetItemCreate]] = None


# ---------------------------------------------------------------------------
# VehicleConHistorial — needs OrderResumen defined first
# ---------------------------------------------------------------------------

class VehicleConHistorial(BaseModel):
    id: int
    matricula: str
    marca: str
    modelo: str
    año: int
    cliente_id: int
    cliente: ClienteOut
    ordenes: List[OrderResumen] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# ClienteConVehiculos — needs VehicleOut defined first
# ---------------------------------------------------------------------------

class ClienteConVehiculos(ClienteOut):
    vehiculos: List[VehicleOut] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Config schema
# ---------------------------------------------------------------------------

class ConfigMap(RootModel[dict[str, str]]):
    pass


# ---------------------------------------------------------------------------
# Rebuild models with forward references
# ---------------------------------------------------------------------------

ClienteOut.model_rebuild()
ClienteConVehiculos.model_rebuild()
VehicleOut.model_rebuild()
VehicleConCliente.model_rebuild()
VehicleConHistorial.model_rebuild()
OrderResumen.model_rebuild()
OrderOut.model_rebuild()
BudgetItemOut.model_rebuild()
