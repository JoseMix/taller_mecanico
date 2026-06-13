from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, String, Integer, Float, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    apellido: Mapped[str] = mapped_column(String, nullable=False)
    nif_dni: Mapped[str] = mapped_column(String, nullable=False)
    telefono: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    direccion: Mapped[str] = mapped_column(String, nullable=False)
    localidad: Mapped[str] = mapped_column(String, nullable=False)
    provincia: Mapped[str] = mapped_column(String, nullable=False)

    vehiculos: Mapped[List["Vehicle"]] = relationship(
        "Vehicle", back_populates="cliente"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clientes.id"), nullable=False
    )
    matricula: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    marca: Mapped[str] = mapped_column(String, nullable=False)
    modelo: Mapped[str] = mapped_column(String, nullable=False)
    año: Mapped[int] = mapped_column(Integer, nullable=False)

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="vehiculos")
    ordenes: Mapped[List["Order"]] = relationship(
        "Order", back_populates="vehicle"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero_orden: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    kilometraje: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notas_internas: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fecha_entrada: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    fecha_entrega: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="ordenes")
    items: Mapped[List["BudgetItem"]] = relationship(
        "BudgetItem", back_populates="order", cascade="all, delete-orphan"
    )


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    concepto: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    cantidad: Mapped[float] = mapped_column(Float, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    es_cargo_cancelacion: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    order: Mapped["Order"] = relationship("Order", back_populates="items")


class Config(Base):
    __tablename__ = "config"

    clave: Mapped[str] = mapped_column(String, primary_key=True)
    valor: Mapped[str] = mapped_column(String, nullable=False)
