<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import type { components } from '@/types/api'
import { useOrdersStore } from '@/stores/orders.store'
import { guardInt } from '@/lib/inputGuards'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import BudgetItemForm from '@/components/BudgetItemForm.vue'
import CancellationDialog from '@/components/CancellationDialog.vue'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type OrderResumen = components['schemas']['OrderResumen']
type EstadoOrden = components['schemas']['EstadoOrden']
type BudgetItem = components['schemas']['BudgetItem']
type TipoItem = components['schemas']['TipoItem']

const LOCK_STATES = new Set<EstadoOrden>(['en_reparacion', 'finalizada', 'entregado', 'rechazado'])

const ESTADO_TOAST: Partial<Record<EstadoOrden, string>> = {
  presupuestado: 'Presupuesto enviado al cliente',
  en_reparacion: 'Reparación iniciada',
  finalizada: 'Reparación finalizada',
  entregado: 'Vehículo entregado al cliente',
  rechazado: 'Orden rechazada',
}

const ESTADO_LABELS: Record<EstadoOrden, string> = {
  recibida: 'Recibida',
  presupuestado: 'Presupuestado',
  en_reparacion: 'En Reparación',
  finalizada: 'Finalizada',
  entregado: 'Entregado',
  rechazado: 'Rechazado',
}

const ESTADO_CLASSES: Record<EstadoOrden, string> = {
  recibida: 'bg-slate-100 text-slate-700 border-slate-300',
  presupuestado: 'bg-blue-100 text-blue-700 border-blue-300',
  en_reparacion: 'bg-violet-100 text-violet-700 border-violet-300',
  finalizada: 'bg-amber-100 text-amber-700 border-amber-300',
  entregado: 'bg-green-100 text-green-700 border-green-300',
  rechazado: 'bg-red-100 text-red-700 border-red-300',
}

const props = defineProps<{
  open: boolean
  order: OrderResumen | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  close: []
}>()

const ordersStore = useOrdersStore()

// --------------- local editable fields ---------------
const editDescripcion = ref('')
const editKilometraje = ref<number | null>(null)
const editNotas = ref<string | null>(null)
const isSavingFields = ref(false)
const fieldError = ref<string | null>(null)
const fieldSuccess = ref(false)

// --------------- items ---------------
const localItems = ref<BudgetItem[]>([])
const isLoadingItems = ref(false)
const itemsError = ref<string | null>(null)

// item being edited (by id, null = none)
const editingItemId = ref<number | null>(null)
const editingItemForm = ref<{ concepto: string; tipo: TipoItem; cantidad: number; precio_unitario: number }>({
  concepto: '',
  tipo: 'mano_obra',
  cantidad: 1,
  precio_unitario: 0,
})
const isSavingItem = ref(false)

// new item form
const showAddForm = ref(false)
const newItemForm = ref<{ concepto: string; tipo: TipoItem; cantidad: number; precio_unitario: number }>({
  concepto: '',
  tipo: 'mano_obra',
  cantidad: 1,
  precio_unitario: 0,
})
const isSavingNew = ref(false)

// --------------- state transitions ---------------
const isChangingEstado = ref(false)
const estadoError = ref<string | null>(null)

// --------------- cancellation dialog ---------------
const showCancellationDialog = ref(false)

// --------------- computed ---------------
const isLocked = computed(() => props.order ? LOCK_STATES.has(props.order.estado) : false)
const kmEditable = computed(() =>
  props.order?.estado === 'recibida' || props.order?.estado === 'presupuestado',
)

const estadoLabel = computed(() =>
  props.order ? (ESTADO_LABELS[props.order.estado] ?? props.order.estado) : '',
)
const estadoClass = computed(() =>
  props.order
    ? (ESTADO_CLASSES[props.order.estado] ?? 'bg-gray-100 text-gray-700 border-gray-300')
    : '',
)

const vehicleInfo = computed(() => {
  const v = props.order?.vehiculo
  if (!v) return ''
  const año = (v as Record<string, unknown>)['año'] as number | undefined
  return `${v.marca} ${v.modelo}${año ? ' ' + año : ''}`
})

const clienteInfo = computed(() => {
  const c = props.order?.vehiculo?.cliente
  if (!c) return null
  return c
})

const hasCancelacionItems = computed(() =>
  localItems.value.some((i) => i.es_cargo_cancelacion),
)

const regularItems = computed(() => localItems.value.filter((i) => !i.es_cargo_cancelacion))
const cancelacionItems = computed(() => localItems.value.filter((i) => i.es_cargo_cancelacion))

// --------------- helpers ---------------
function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatCurrency(val: number) {
  return val.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €'
}

function formatSubtotal(item: BudgetItem) {
  const sub = item.subtotal ?? item.cantidad * item.precio_unitario
  return formatCurrency(sub)
}

// --------------- watchers ---------------
// Reset editable fields only when the selected ORDER changes (new ID).
// Watching the full object would fire on every polling update (new reference, same data)
// and wipe whatever the user was typing.
watch(
  () => props.order?.id,
  async (id) => {
    if (!id) return
    const order = props.order!
    editDescripcion.value = order.descripcion ?? ''
    editKilometraje.value = order.kilometraje ?? null
    editNotas.value = order.notas_internas ?? null
    fieldError.value = null
    fieldSuccess.value = false
    estadoError.value = null
    showAddForm.value = false
    editingItemId.value = null
    await fetchItems()
  },
  { immediate: false },
)

// Also load items when the sheet opens
watch(
  () => props.open,
  async (open) => {
    if (open && props.order) {
      editDescripcion.value = props.order.descripcion ?? ''
      editKilometraje.value = props.order.kilometraje ?? null
      editNotas.value = props.order.notas_internas ?? null
      await fetchItems()
    }
  },
)

// After cancellation confirmed, re-fetch
async function onCancellationConfirmed() {
  showCancellationDialog.value = false
  if (props.order) await fetchItems()
}

// --------------- actions ---------------
async function fetchItems() {
  if (!props.order) return
  isLoadingItems.value = true
  itemsError.value = null
  try {
    // GET /ordenes/{id} returns full Order including items
    const res = await fetch(`${API_BASE}/ordenes/${props.order.id}`)
    if (!res.ok) throw new Error('No se pudieron cargar los items')
    const data = await res.json()
    localItems.value = data.items ?? []
  } catch (e) {
    itemsError.value = e instanceof Error ? e.message : 'Error al cargar items'
  } finally {
    isLoadingItems.value = false
  }
}

async function handleSaveFields() {
  if (!props.order) return
  isSavingFields.value = true
  fieldError.value = null
  fieldSuccess.value = false
  try {
    await ordersStore.updateOrden(props.order.id, {
      descripcion: editDescripcion.value,
      kilometraje: editKilometraje.value ?? null,
      notas_internas: editNotas.value ?? null,
    })
    fieldSuccess.value = true
    setTimeout(() => { fieldSuccess.value = false }, 2000)
    toast.success('Cambios guardados')
  } catch (e) {
    fieldError.value = e instanceof Error ? e.message : 'Error al guardar'
    toast.error(fieldError.value)
  } finally {
    isSavingFields.value = false
  }
}

async function handleChangeEstado(nuevo_estado: EstadoOrden) {
  if (!props.order) return
  isChangingEstado.value = true
  estadoError.value = null
  try {
    await ordersStore.updateEstado(props.order.id, nuevo_estado)
    await fetchItems()
    toast.success(ESTADO_TOAST[nuevo_estado] ?? 'Estado actualizado')
  } catch (e) {
    estadoError.value = e instanceof Error ? e.message : 'Error al cambiar estado'
    toast.error(estadoError.value)
  } finally {
    isChangingEstado.value = false
  }
}

function handleDownloadPdf() {
  if (!props.order) return
  window.open(`${API_BASE}/ordenes/${props.order.id}/pdf`, '_blank')
}

// ---- add new item ----
function openAddForm() {
  newItemForm.value = { concepto: '', tipo: 'mano_obra', cantidad: 1, precio_unitario: 0 }
  showAddForm.value = true
}

async function handleSaveNew() {
  if (!props.order) return
  isSavingNew.value = true
  itemsError.value = null
  try {
    await ordersStore.addItem(props.order.id, {
      concepto: newItemForm.value.concepto,
      tipo: newItemForm.value.tipo,
      cantidad: newItemForm.value.cantidad,
      precio_unitario: newItemForm.value.precio_unitario,
      es_cargo_cancelacion: false,
    })
    showAddForm.value = false
    await fetchItems()
    toast.success('Concepto añadido al presupuesto')
  } catch (e) {
    itemsError.value = e instanceof Error ? e.message : 'Error al añadir item'
    toast.error(itemsError.value)
  } finally {
    isSavingNew.value = false
  }
}

// ---- edit existing item ----
function startEditItem(item: BudgetItem) {
  editingItemId.value = item.id
  editingItemForm.value = {
    concepto: item.concepto,
    tipo: item.tipo,
    cantidad: item.cantidad,
    precio_unitario: item.precio_unitario,
  }
}

function cancelEditItem() {
  editingItemId.value = null
}

async function handleSaveItem(itemId: number) {
  if (!props.order) return
  isSavingItem.value = true
  itemsError.value = null
  try {
    await ordersStore.updateItem(props.order.id, itemId, {
      concepto: editingItemForm.value.concepto,
      tipo: editingItemForm.value.tipo,
      cantidad: editingItemForm.value.cantidad,
      precio_unitario: editingItemForm.value.precio_unitario,
    })
    editingItemId.value = null
    await fetchItems()
    toast.success('Concepto actualizado')
  } catch (e) {
    itemsError.value = e instanceof Error ? e.message : 'Error al actualizar item'
    toast.error(itemsError.value)
  } finally {
    isSavingItem.value = false
  }
}

async function handleDeleteItem(itemId: number) {
  if (!props.order) return
  itemsError.value = null
  try {
    await ordersStore.deleteItem(props.order.id, itemId)
    await fetchItems()
    toast.success('Concepto eliminado')
  } catch (e) {
    itemsError.value = e instanceof Error ? e.message : 'Error al eliminar item'
    toast.error(itemsError.value)
  }
}

function handleSheetClose() {
  emit('update:open', false)
  emit('close')
}
</script>

<template>
  <Sheet :open="open" @update:open="handleSheetClose">
    <SheetContent side="right" class="w-full sm:max-w-xl overflow-y-auto flex flex-col gap-0 p-0">
      <div v-if="!order" class="flex-1 flex items-center justify-center text-muted-foreground text-sm p-6">
        No hay orden seleccionada
      </div>

      <template v-else>
        <!-- Header -->
        <SheetHeader class="px-6 pt-6 pb-4 border-b">
          <div class="flex items-start justify-between gap-2 pr-6">
            <div>
              <SheetTitle class="text-xl font-mono font-bold tracking-tight">
                {{ order.numero_orden }}
              </SheetTitle>
              <SheetDescription class="text-xs text-muted-foreground mt-0.5">
                Entrada: {{ formatDate(order.fecha_entrada) }}
              </SheetDescription>
            </div>
            <span
              :class="['inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium mt-1', estadoClass]"
            >
              {{ estadoLabel }}
            </span>
          </div>
        </SheetHeader>

        <div class="flex flex-col gap-4 px-6 py-4 overflow-y-auto flex-1">

          <!-- Section: Vehicle + Client -->
          <section>
            <h3 class="text-xs font-semibold uppercase text-muted-foreground tracking-wide mb-2">Vehículo y cliente</h3>
            <div class="rounded-md bg-muted/40 border border-border p-3 space-y-1 text-sm">
              <div class="flex items-center gap-3">
                <span class="font-bold text-base">{{ order.vehiculo?.matricula ?? '—' }}</span>
                <span class="text-muted-foreground">{{ vehicleInfo }}</span>
              </div>
              <div v-if="order.kilometraje" class="text-xs text-muted-foreground">
                {{ order.kilometraje.toLocaleString('es-ES') }} km
              </div>
              <Separator class="my-1" />
              <div v-if="clienteInfo" class="space-y-0.5">
                <div class="font-medium">{{ clienteInfo.apellido }}, {{ clienteInfo.nombre }}</div>
                <div class="text-xs text-muted-foreground">
                  Tel: {{ clienteInfo.telefono }} &bull; DNI: {{ clienteInfo.nif_dni }}
                </div>
              </div>
            </div>
          </section>

          <!-- Section: Editable fields -->
          <section>
            <h3 class="text-xs font-semibold uppercase text-muted-foreground tracking-wide mb-2">Detalles de la orden</h3>
            <div class="space-y-2">
              <div>
                <label class="block text-xs font-medium mb-1">Descripción</label>
                <textarea
                  v-model="editDescripcion"
                  rows="2"
                  class="w-full rounded border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-ring"
                  placeholder="Descripción de la avería o trabajo a realizar"
                />
              </div>
              <div>
                <label class="block text-xs font-medium mb-1">Kilometraje</label>
                <input
                  v-if="kmEditable"
                  v-model.number="editKilometraje"
                  type="number"
                  inputmode="numeric"
                  min="0"
                  class="w-full rounded border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                  placeholder="Km del vehículo"
                  @keydown="guardInt"
                />
                <p v-else class="px-3 py-2 text-sm text-muted-foreground bg-muted/40 rounded border border-border">
                  {{ editKilometraje != null ? editKilometraje.toLocaleString('es-ES') + ' km' : '—' }}
                </p>
              </div>
              <div>
                <label class="block text-xs font-medium mb-1">Notas internas</label>
                <textarea
                  v-model="editNotas"
                  rows="2"
                  class="w-full rounded border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-ring"
                  placeholder="Notas solo para el taller"
                />
              </div>

              <div v-if="fieldError" class="text-xs text-destructive">{{ fieldError }}</div>
              <div v-if="fieldSuccess" class="text-xs text-green-600">Guardado correctamente</div>

              <Button
                size="sm"
                :disabled="isSavingFields"
                @click="handleSaveFields"
              >
                {{ isSavingFields ? 'Guardando…' : 'Guardar cambios' }}
              </Button>
            </div>
          </section>

          <!-- Section: Budget items -->
          <section>
            <h3 class="text-xs font-semibold uppercase text-muted-foreground tracking-wide mb-2">Presupuesto</h3>

            <div v-if="isLoadingItems" class="text-xs text-muted-foreground animate-pulse py-2">
              Cargando items…
            </div>
            <div v-else-if="itemsError" class="text-xs text-destructive py-2">{{ itemsError }}</div>

            <!-- Regular items -->
            <div v-if="regularItems.length > 0" class="space-y-1 mb-2">
              <template v-for="item in regularItems" :key="item.id">
                <!-- Edit mode -->
                <BudgetItemForm
                  v-if="editingItemId === item.id"
                  v-model="editingItemForm"
                  :is-loading="isSavingItem"
                  @save="handleSaveItem(item.id)"
                  @cancel="cancelEditItem"
                />
                <!-- View mode -->
                <div
                  v-else
                  class="flex items-center gap-2 rounded-md border border-border bg-muted/10 px-3 py-2 text-sm"
                >
                  <div class="flex-1 min-w-0">
                    <span class="font-medium truncate">{{ item.concepto }}</span>
                    <span class="ml-2 text-xs text-muted-foreground">
                      ({{ item.tipo === 'mano_obra' ? 'Mano de obra' : 'Pieza' }})
                    </span>
                  </div>
                  <div class="text-xs text-muted-foreground shrink-0">
                    {{ item.cantidad }} × {{ formatCurrency(item.precio_unitario) }}
                  </div>
                  <div class="font-semibold text-sm shrink-0">
                    {{ formatSubtotal(item) }}
                  </div>
                  <div v-if="!isLocked" class="flex gap-1 shrink-0">
                    <button
                      class="text-xs text-muted-foreground hover:text-primary px-1"
                      @click="startEditItem(item)"
                    >
                      Editar
                    </button>
                    <button
                      class="text-xs text-muted-foreground hover:text-destructive px-1"
                      @click="handleDeleteItem(item.id)"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              </template>
            </div>

            <!-- Cancellation charge items -->
            <div v-if="cancelacionItems.length > 0" class="space-y-1 mb-2">
              <div
                v-for="item in cancelacionItems"
                :key="item.id"
                class="flex items-center gap-2 rounded-md border border-orange-200 bg-orange-50 px-3 py-2 text-sm"
              >
                <div class="flex-1 min-w-0">
                  <span class="font-medium truncate">{{ item.concepto }}</span>
                  <span class="ml-2 inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-700 border border-orange-200">
                    Cargo cancelación
                  </span>
                </div>
                <div class="text-xs text-muted-foreground shrink-0">
                  {{ item.cantidad }} × {{ formatCurrency(item.precio_unitario) }}
                </div>
                <div class="font-semibold text-sm shrink-0">
                  {{ formatSubtotal(item) }}
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div
              v-if="!isLoadingItems && regularItems.length === 0 && cancelacionItems.length === 0"
              class="text-xs text-muted-foreground py-2 text-center border border-dashed border-border rounded-md"
            >
              No hay items en el presupuesto
            </div>

            <!-- Total -->
            <div
              v-if="localItems.length > 0"
              class="flex justify-end text-sm font-semibold pt-1 pb-2"
            >
              Total: {{ formatCurrency(localItems.reduce((s, i) => s + (i.subtotal ?? i.cantidad * i.precio_unitario), 0)) }}
            </div>

            <!-- Add new item form -->
            <BudgetItemForm
              v-if="showAddForm && !isLocked"
              v-model="newItemForm"
              :is-loading="isSavingNew"
              @save="handleSaveNew"
              @cancel="showAddForm = false"
            />

            <!-- Añadir concepto button -->
            <Button
              v-if="!isLocked && !showAddForm"
              size="sm"
              variant="outline"
              @click="openAddForm"
            >
              + Añadir concepto
            </Button>
          </section>

          <Separator />

          <!-- Section: Actions -->
          <section>
            <h3 class="text-xs font-semibold uppercase text-muted-foreground tracking-wide mb-2">Acciones</h3>

            <div v-if="estadoError" class="text-xs text-destructive mb-2">{{ estadoError }}</div>

            <div class="flex flex-wrap gap-2">
              <!-- recibida -->
              <template v-if="order.estado === 'recibida'">
                <Button
                  size="sm"
                  :disabled="isChangingEstado"
                  @click="handleChangeEstado('presupuestado')"
                >
                  Enviar presupuesto
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  :disabled="isChangingEstado"
                  @click="handleChangeEstado('rechazado')"
                >
                  Rechazar
                </Button>
              </template>

              <!-- presupuestado -->
              <template v-else-if="order.estado === 'presupuestado'">
                <Button
                  size="sm"
                  :disabled="isChangingEstado"
                  @click="handleChangeEstado('en_reparacion')"
                >
                  Aprobar
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  :disabled="isChangingEstado"
                  @click="handleChangeEstado('rechazado')"
                >
                  Rechazar
                </Button>
              </template>

              <!-- en_reparacion -->
              <template v-else-if="order.estado === 'en_reparacion'">
                <Button
                  size="sm"
                  :disabled="isChangingEstado"
                  @click="handleChangeEstado('finalizada')"
                >
                  Finalizar
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  :disabled="isChangingEstado"
                  @click="showCancellationDialog = true"
                >
                  Cancelar reparación
                </Button>
              </template>

              <!-- finalizada -->
              <template v-else-if="order.estado === 'finalizada'">
                <Button
                  size="sm"
                  :disabled="isChangingEstado"
                  @click="handleChangeEstado('entregado')"
                >
                  Marcar como entregado
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  @click="handleDownloadPdf"
                >
                  Descargar factura
                </Button>
              </template>

              <!-- entregado -->
              <template v-else-if="order.estado === 'entregado'">
                <Button
                  size="sm"
                  variant="outline"
                  @click="handleDownloadPdf"
                >
                  Descargar factura
                </Button>
              </template>

              <!-- rechazado -->
              <template v-else-if="order.estado === 'rechazado'">
                <Button
                  v-if="hasCancelacionItems"
                  size="sm"
                  variant="outline"
                  @click="handleDownloadPdf"
                >
                  Descargar factura cancelación
                </Button>
                <span v-else class="text-xs text-muted-foreground">
                  Orden rechazada sin cargos de cancelación
                </span>
              </template>

              <!-- loading indicator -->
              <span v-if="isChangingEstado" class="text-xs text-muted-foreground animate-pulse self-center">
                Procesando…
              </span>
            </div>
          </section>
        </div>
      </template>
    </SheetContent>
  </Sheet>

  <!-- Cancellation dialog (outside SheetContent to avoid portal nesting issues) -->
  <CancellationDialog
    v-if="order"
    v-model:open="showCancellationDialog"
    :order-id="order.id"
    @confirmed="onCancellationConfirmed"
  />
</template>
