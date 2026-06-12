# Diseño: App de Gestión de Taller Mecánico

**Fecha:** 2026-06-12  
**Estado:** Aprobado

---

## 1. Descripción general

Aplicación web para talleres mecánicos que gestiona las órdenes de trabajo mediante un tablero Kanban. Permite crear, presupuestar, seguir y facturar las reparaciones de vehículos, con búsqueda por matrícula e historial de órdenes por cliente.

**Sin autenticación.** Acceso libre en red local (LAN del taller). Despliegue local: servidor FastAPI + frontend Vue accesibles desde cualquier dispositivo en la WiFi del taller.

---

## 2. Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue 3 + Composition API + TypeScript |
| UI | shadcn-vue + Tailwind CSS |
| Estado | Pinia |
| Build | Vite |
| Backend | Python + FastAPI |
| ORM | SQLAlchemy |
| Base de datos | SQLite |
| PDF | WeasyPrint (renderiza plantilla Jinja2 a PDF) |
| API spec | OpenAPI 3.1.0 — YAML escrito a mano (API-first) |
| Tipos TS | generados desde el YAML con `openapi-typescript` |

---

## 3. Estructura del proyecto

```
taller-app/
├── frontend/
│   ├── src/
│   │   ├── components/       # KanbanBoard, OrderCard, OrderDetailSheet, SearchPanel...
│   │   ├── composables/      # useOrders.ts, usePolling.ts
│   │   ├── stores/           # orders.store.ts (Pinia)
│   │   ├── views/            # KanbanView.vue, SearchView.vue, AjustesView.vue
│   │   └── types/            # generados por openapi-typescript desde el spec YAML
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── models.py         # modelos SQLAlchemy
│   │   ├── schemas.py        # schemas Pydantic
│   │   ├── crud.py           # operaciones de base de datos
│   │   ├── routes/
│   │   │   ├── clientes.py
│   │   │   ├── vehiculos.py
│   │   │   ├── ordenes.py
│   │   │   ├── items.py
│   │   │   ├── pdf.py
│   │   │   └── config.py
│   │   ├── pdf_templates/    # plantillas Jinja2 para WeasyPrint
│   │   └── main.py           # app FastAPI + CORS
│   └── requirements.txt
│
├── openapi/
│   └── spec.yaml             # spec OpenAPI 3.1.0 — fuente de verdad
│
└── docs/
    └── superpowers/specs/
        └── 2026-06-12-taller-mecanico-design.md
```

---

## 4. Modelo de datos

### Cliente
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| nombre | TEXT | |
| apellido | TEXT | |
| nif_dni | TEXT | aparece en factura PDF |
| telefono | TEXT | |
| email | TEXT NULL | opcional |
| direccion | TEXT | |
| localidad | TEXT | |
| provincia | TEXT | |

### Vehicle
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| cliente_id | FK → Cliente | |
| matricula | TEXT UNIQUE | |
| marca | TEXT | |
| modelo | TEXT | |
| año | INTEGER | |

### Order
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| numero_orden | TEXT UNIQUE | formato `YYYY-NNN`, generado en backend |
| vehicle_id | FK → Vehicle | |
| estado | TEXT ENUM | ver sección 5 |
| descripcion | TEXT | descripción del problema |
| kilometraje | INTEGER NULL | km registrados al entrar el vehículo |
| notas_internas | TEXT NULL | notas del mecánico, no aparecen en factura |
| fecha_entrada | DATETIME | automática al crear |
| fecha_actualizacion | DATETIME | actualizada en cada cambio |
| fecha_entrega | DATETIME NULL | se rellena al pasar a `entregado` |

### BudgetItem
| Campo | Tipo | Notas |
|-------|------|-------|
| id | INTEGER PK | |
| order_id | FK → Order | |
| concepto | TEXT | |
| tipo | ENUM | `mano_obra` o `pieza` |
| cantidad | NUMERIC | horas o unidades |
| precio_unitario | NUMERIC | |
| es_cargo_cancelacion | BOOLEAN | `false` = item normal; `true` = cobro al cancelar |

### Config (clave-valor)
| Campo | Tipo | Notas |
|-------|------|-------|
| clave | TEXT PK | ej: `tarifa_hora`, `nombre_taller`, `cif_taller`, `direccion_taller` |
| valor | TEXT | |

**Relaciones:** `Cliente (1) → (N) Vehicle (1) → (N) Order (1) → (N) BudgetItem`

**Cálculo del total:** `SUM(cantidad × precio_unitario)` sobre los items relevantes — calculado en runtime, no persiste en base de datos.

---

## 5. Máquina de estados

### Estados válidos
`recibida` · `presupuestado` · `en_reparacion` · `finalizada` · `entregado` · `rechazado`

### Transiciones permitidas
```
recibida      → presupuestado   (mecánico pulsa "Enviar presupuesto"; prerequisito: ≥1 BudgetItem)
recibida      → rechazado       (cliente desiste antes del presupuesto)
presupuestado → en_reparacion   (cliente acepta presupuesto)
presupuestado → rechazado       (cliente rechaza presupuesto)
en_reparacion → finalizada      (trabajo completado)
en_reparacion → rechazado       (cliente cancela durante reparación)
finalizada    → entregado       (cliente recoge y paga)
```

`entregado` y `rechazado` son estados terminales — no admiten ninguna transición ni modificación.

### Reglas de negocio
- No se puede pasar a `en_reparacion` sin al menos 1 `BudgetItem` con `es_cargo_cancelacion=false`.
- Un vehículo solo puede tener 1 orden cuyo estado no sea `entregado` ni `rechazado`.
- Los `BudgetItem` con `es_cargo_cancelacion=false` no son editables cuando el estado es `en_reparacion`, `finalizada`, `entregado` o `rechazado`.

### Flujo de rechazo según origen

| Desde | Cobro | Acción en backend |
|-------|-------|-------------------|
| `recibida` | Sin cobro | Orden → `rechazado` directamente |
| `presupuestado` | 30 min mano de obra | Backend crea automáticamente 1 `BudgetItem` con `es_cargo_cancelacion=true`: concepto "Cargo por diagnóstico", tipo `mano_obra`, cantidad 0.5, precio_unitario = `tarifa_hora` de Config |
| `en_reparacion` | Horas usadas + materiales reales | El mecánico introduce los items reales en un formulario; se guardan con `es_cargo_cancelacion=true`. Los items originales quedan intactos como referencia |

---

## 6. API REST — OpenAPI 3.1.0 (API-first)

El fichero `openapi/spec.yaml` es la **fuente de verdad**. FastAPI lo sirve en `/openapi.yaml`. Los tipos TypeScript del frontend se generan automáticamente con `openapi-typescript`.

### Endpoints

```
# Clientes
GET    /clientes                         listar / buscar por nombre
POST   /clientes                         crear cliente
GET    /clientes/{id}                    detalle + vehículos
PUT    /clientes/{id}                    editar cliente

# Vehículos
POST   /vehiculos                        crear (requiere cliente_id)
GET    /vehiculos/{id}                   detalle + historial de órdenes
GET    /vehiculos/buscar?matricula=      búsqueda por matrícula

# Órdenes
GET    /ordenes                          para el Kanban: estados no terminales + entregado/rechazado últimos 7 días
POST   /ordenes                          crear orden (requiere vehiculo_id)
GET    /ordenes/{id}                     detalle completo
PUT    /ordenes/{id}                     editar descripcion / kilometraje / notas_internas
PATCH  /ordenes/{id}/estado              cambiar estado (valida reglas de negocio)
DELETE /ordenes/{id}                     solo si estado = recibida

# Items de presupuesto
POST   /ordenes/{id}/items               añadir item
PUT    /ordenes/{id}/items/{item_id}     editar item
DELETE /ordenes/{id}/items/{item_id}     eliminar item

# PDF
GET    /ordenes/{id}/pdf                 descarga PDF (factura o cancelación según estado)

# Configuración del taller
GET    /config                           obtener configuración
PUT    /config                           actualizar configuración
```

Las violaciones de reglas de negocio devuelven `422 Unprocessable Entity` con mensaje descriptivo.

---

## 7. Frontend — Vistas y componentes principales

### Vistas (Vue Router)
- `/` → `KanbanView` — tablero principal
- `/buscar` → `SearchView` — búsqueda por matrícula + historial
- `/ajustes` → `AjustesView` — configuración del taller (tarifa/hora, nombre, CIF, dirección)

### Componentes clave
- `KanbanBoard` — 6 carriles (uno por estado), se refresca cada 30 s con `usePolling`
- `OrderCard` — tarjeta en el Kanban; muestra matrícula, cliente, modelo, total presupuesto y badge 🔒 si está bloqueado
- `OrderDetailSheet` — Sheet de shadcn-vue que se abre al pulsar una tarjeta; muestra datos completos, items del presupuesto y botones de acción según estado
- `CancellationDialog` — Dialog de shadcn-vue para introducir cobros reales al cancelar desde `en_reparacion`
- `SearchPanel` — buscador por matrícula con historial de todas las órdenes del vehículo

### Componentes shadcn-vue usados
`Sheet` · `Dialog` · `Button` · `Badge` · `Card` · `Table` · `Input` · `Label` · `Separator`

### Sincronización
Un composable `usePolling(intervalMs = 30000)` refresca el store de Pinia en segundo plano. Las mutaciones (crear orden, cambiar estado, editar items) actualizan el servidor y el store local de forma inmediata sin esperar al siguiente poll.

---

## 8. PDF

Generado en el backend con **WeasyPrint** sobre plantillas Jinja2.

| Tipo | Cuando | Contenido |
|------|--------|-----------|
| Factura | Estado = `entregado` | Items con `es_cargo_cancelacion=false` + IVA 21% |
| Factura de cancelación | Estado = `rechazado` | Items con `es_cargo_cancelacion=true` + IVA 21% |

Ambos tipos incluyen: datos del taller (de `Config`), datos del cliente (nombre, apellido, NIF, dirección), datos del vehículo (matrícula, marca, modelo, año, km) y tabla de conceptos con totales.

El endpoint `GET /ordenes/{id}/pdf` devuelve el fichero con `Content-Disposition: attachment; filename="factura-YYYY-NNN.pdf"`.

El IVA (21%) se calcula en el backend al generar el PDF — no se persiste en base de datos.

---

## 9. Página de Ajustes

Ruta `/ajustes`. Gestiona la tabla `Config` de SQLite con los siguientes campos:

| Clave | Descripción |
|-------|-------------|
| `tarifa_hora` | Tarifa de mano de obra (€/h) — usada para el cargo automático de 30 min |
| `nombre_taller` | Aparece en cabecera del PDF |
| `cif_taller` | Aparece en cabecera del PDF |
| `direccion_taller` | Aparece en cabecera del PDF |

---

## 10. Testing

### Backend (pytest)
- Tests unitarios de la lógica de transición de estados
- Tests de integración sobre endpoints críticos con `httpx` y SQLite en memoria
- Cobertura prioritaria: reglas de bloqueo de presupuesto, unicidad de orden activa por vehículo, cargo automático al rechazar desde `presupuestado`

### Frontend (Vitest + Vue Test Utils)
- Tests de composables (`useOrders`, `usePolling`)
- Tests de stores Pinia
- No se testean componentes UI — el tiempo se invierte en tests de backend donde vive la lógica de negocio

---

## 11. Decisiones descartadas

| Alternativa | Motivo de descarte |
|-------------|-------------------|
| WebSockets para Kanban en tiempo real | Overkill para un taller pequeño; polling de 30s es suficiente en LAN |
| FastAPI sirviendo el frontend (servidor único) | Complica el workflow de desarrollo; se mantienen procesos separados |
| Autenticación / multi-usuario | Fuera de scope; taller único sin roles |
| Persistir el total del presupuesto en BD | Genera inconsistencias; se calcula en runtime |
| IVA persistido en BD | Se calcula al generar el PDF para evitar inconsistencias si cambia el tipo |
