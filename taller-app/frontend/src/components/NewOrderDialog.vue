<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import type { components } from '@/types/api'
import { apiGet, apiPost } from '@/lib/api'
import { useOrdersStore } from '@/stores/orders.store'
import { guardInt } from '@/lib/inputGuards'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type VehicleConHistorial = components['schemas']['VehicleConHistorial']
type Cliente = components['schemas']['Cliente']
type Vehicle = components['schemas']['Vehicle']

// ─── Props & Emits ────────────────────────────────────────────────────────────

const props = defineProps<{ open: boolean }>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  created: []
}>()

// ─── Store ────────────────────────────────────────────────────────────────────

const ordersStore = useOrdersStore()

// ─── Step control ─────────────────────────────────────────────────────────────
// step 1 = vehicle search
// step 2 = create client + vehicle (vehicle not found)
// step 3 = order description
type Step = 1 | 2 | 3
const step = ref<Step>(1)

// ─── Step 1: Vehicle search ────────────────────────────────────────────────────

const matriculaInput = ref('')
const searchLoading = ref(false)
const searchError = ref<string | null>(null)
const vehicleNotFound = ref(false)
const foundVehicle = ref<VehicleConHistorial | null>(null)

watch(matriculaInput, (val) => {
  if (!val.trim()) {
    vehicleNotFound.value = false
    foundVehicle.value = null
    searchError.value = null
  }
})

function handleSearchKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && matriculaInput.value.trim().length >= 6) {
    searchNow()
  }
}

async function searchNow() {
  if (!matriculaInput.value.trim()) return
  searchLoading.value = true
  searchError.value = null
  vehicleNotFound.value = false
  foundVehicle.value = null
  try {
    const results = await apiGet<VehicleConHistorial[]>(
      `/vehiculos/buscar?matricula=${encodeURIComponent(matriculaInput.value.trim())}`,
    )
    if (!results || results.length === 0) {
      vehicleNotFound.value = true
    } else {
      foundVehicle.value = results[0]
      step.value = 3
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : ''
    if (msg.toLowerCase().includes('not found') || msg.includes('404') || msg === 'Not Found') {
      vehicleNotFound.value = true
    } else {
      searchError.value = msg || 'Error al buscar el vehículo'
    }
  } finally {
    searchLoading.value = false
  }
}

function goToCreateNewVehicle() {
  // Pre-fill the matricula from the search input
  clientForm.value = emptyClientForm()
  vehicleForm.value = { ...emptyVehicleForm(), matricula: matriculaInput.value.trim() }
  step.value = 2
}

// ─── Step 2: Create Client + Vehicle ─────────────────────────────────────────

interface ClientForm {
  nombre: string
  apellido: string
  nif_dni: string
  telefono: string
  email: string
  direccion: string
  localidad: string
  provincia: string
}

interface VehicleForm {
  matricula: string
  marca: string
  modelo: string
  año: string
}

function emptyClientForm(): ClientForm {
  return {
    nombre: '',
    apellido: '',
    nif_dni: '',
    telefono: '',
    email: '',
    direccion: '',
    localidad: '',
    provincia: '',
  }
}

function emptyVehicleForm(): VehicleForm {
  return { matricula: '', marca: '', modelo: '', año: '' }
}

const clientForm = ref<ClientForm>(emptyClientForm())
const vehicleForm = ref<VehicleForm>(emptyVehicleForm())
const step2Error = ref<string | null>(null)
const step2Loading = ref(false)

// ─── Per-field validation ──────────────────────────────────────────────────

const touched = ref<Record<string, boolean>>({})

function touch(field: string) {
  touched.value[field] = true
}

function validateTelefono(val: string): string | null {
  const v = val.trim()
  if (!v) return 'El teléfono es obligatorio'
  if (!/^\+?\d{7,15}$/.test(v)) return 'Solo dígitos (7-15 cifras, opcionalmente + al inicio)'
  return null
}

function validateEmail(val: string): string | null {
  const v = val.trim()
  if (!v) return null
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'Introduce un email válido (debe contener @)'
  return null
}

const telefonoError = computed(() =>
  touched.value['telefono'] ? validateTelefono(clientForm.value.telefono) : null,
)
const emailError = computed(() =>
  touched.value['email'] ? validateEmail(clientForm.value.email) : null,
)

async function handleStep2Submit() {
  // Show all inline errors immediately on submit attempt
  touch('telefono')
  touch('email')

  step2Error.value = null

  // Inline field errors take priority — let user fix them first
  if (validateTelefono(clientForm.value.telefono) || validateEmail(clientForm.value.email)) {
    return
  }

  // Validate required client fields
  if (
    !clientForm.value.nombre.trim() ||
    !clientForm.value.apellido.trim() ||
    !clientForm.value.nif_dni.trim() ||
    !clientForm.value.telefono.trim() ||
    !clientForm.value.direccion.trim() ||
    !clientForm.value.localidad.trim() ||
    !clientForm.value.provincia.trim()
  ) {
    step2Error.value = 'Por favor, rellena todos los campos obligatorios del cliente.'
    return
  }

  // Validate required vehicle fields
  if (
    !vehicleForm.value.matricula.trim() ||
    !vehicleForm.value.marca.trim() ||
    !vehicleForm.value.modelo.trim() ||
    !vehicleForm.value.año
  ) {
    step2Error.value = 'Por favor, rellena todos los campos obligatorios del vehículo.'
    return
  }

  const añoNum = parseInt(vehicleForm.value.año, 10)
  if (isNaN(añoNum) || añoNum < 1900 || añoNum > new Date().getFullYear() + 1) {
    step2Error.value = 'El año del vehículo no es válido.'
    return
  }

  step2Loading.value = true
  try {
    // POST /clientes
    const clientPayload: Record<string, unknown> = {
      nombre: clientForm.value.nombre.trim(),
      apellido: clientForm.value.apellido.trim(),
      nif_dni: clientForm.value.nif_dni.trim(),
      telefono: clientForm.value.telefono.trim(),
      email: clientForm.value.email.trim() || null,
      direccion: clientForm.value.direccion.trim(),
      localidad: clientForm.value.localidad.trim(),
      provincia: clientForm.value.provincia.trim(),
    }
    const createdCliente = await apiPost<Cliente>('/clientes', clientPayload)

    // POST /vehiculos
    const vehiclePayload = {
      cliente_id: createdCliente.id,
      matricula: vehicleForm.value.matricula.trim(),
      marca: vehicleForm.value.marca.trim(),
      modelo: vehicleForm.value.modelo.trim(),
      año: añoNum,
    }
    const createdVehicle = await apiPost<Vehicle>('/vehiculos', vehiclePayload)

    // Store so step 3 can use it
    createdVehicleId.value = createdVehicle.id
    createdClienteData.value = createdCliente
    step.value = 3
  } catch (e) {
    step2Error.value = e instanceof Error ? e.message : 'Error al crear cliente/vehículo'
  } finally {
    step2Loading.value = false
  }
}

// Vehicle id from new creation path
const createdVehicleId = ref<number | null>(null)
const createdClienteData = ref<Cliente | null>(null)

// ─── Step 3: Order description ─────────────────────────────────────────────────

interface OrderForm {
  descripcion: string
  kilometraje: string
  notas_internas: string
}

const orderForm = ref<OrderForm>({ descripcion: '', kilometraje: '', notas_internas: '' })
const step3Error = ref<string | null>(null)
const step3Loading = ref(false)

function getVehicleId(): number | null {
  if (foundVehicle.value) return foundVehicle.value.id
  if (createdVehicleId.value !== null) return createdVehicleId.value
  return null
}

async function handleStep3Submit() {
  step3Error.value = null

  if (!orderForm.value.descripcion.trim()) {
    step3Error.value = 'La descripción de la avería es obligatoria.'
    return
  }

  const vehiculoId = getVehicleId()
  if (vehiculoId === null) {
    step3Error.value = 'No se encontró el vehículo. Vuelve al paso 1.'
    return
  }

  const km = String(orderForm.value.kilometraje ?? '').trim()
  const kilometrajeNum = km ? parseInt(km, 10) : null
  if (km && isNaN(kilometrajeNum!)) {
    step3Error.value = 'El kilometraje debe ser un número entero.'
    return
  }

  step3Loading.value = true
  try {
    await apiPost('/ordenes', {
      vehicle_id: vehiculoId,
      descripcion: orderForm.value.descripcion.trim(),
      kilometraje: kilometrajeNum,
      notas_internas: orderForm.value.notas_internas.trim() || null,
    })

    await ordersStore.fetchOrders()
    toast.success('Orden de trabajo creada')
    emit('created')
    handleClose()
  } catch (e) {
    step3Error.value = e instanceof Error ? e.message : 'Error al crear la orden'
    toast.error(step3Error.value)
  } finally {
    step3Loading.value = false
  }
}

// ─── Dialog open/close & reset ────────────────────────────────────────────────

function resetAll() {
  step.value = 1
  matriculaInput.value = ''
  searchLoading.value = false
  searchError.value = null
  vehicleNotFound.value = false
  foundVehicle.value = null
  clientForm.value = emptyClientForm()
  vehicleForm.value = emptyVehicleForm()
  step2Error.value = null
  step2Loading.value = false
  touched.value = {}
  createdVehicleId.value = null
  createdClienteData.value = null
  orderForm.value = { descripcion: '', kilometraje: '', notas_internas: '' }
  step3Error.value = null
  step3Loading.value = false
}

function handleClose() {
  emit('update:open', false)
  resetAll()
}

// Reset when dialog opens
watch(
  () => props.open,
  (val) => {
    if (val) resetAll()
  },
)

// ─── Display helpers ──────────────────────────────────────────────────────────

function stepTitle() {
  if (step.value === 1) return 'Nueva Orden de Trabajo'
  if (step.value === 2) return 'Registrar Cliente y Vehículo'
  return 'Detalles de la Orden'
}

function stepDescription() {
  if (step.value === 1) return 'Busca el vehículo por matrícula para comenzar'
  if (step.value === 2) return 'El vehículo no está registrado. Introduce los datos del cliente y vehículo'
  return 'Describe el trabajo a realizar'
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => { if (!v) handleClose() }">
    <DialogContent class="max-w-xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{{ stepTitle() }}</DialogTitle>
        <DialogDescription>{{ stepDescription() }}</DialogDescription>
      </DialogHeader>

      <!-- ── Step indicator ──────────────────────────────────────────────── -->
      <div class="flex items-center justify-center gap-0 my-1">
        <template v-for="n in [1, 2, 3]" :key="n">
          <div class="flex flex-col items-center gap-1.5">
            <span
              class="inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold border-2 transition-all duration-300"
              :class="step === n
                ? 'bg-primary border-primary text-primary-foreground shadow-cyan-glow-sm'
                : step > n
                  ? 'bg-primary/20 border-primary/50 text-primary'
                  : 'bg-muted border-border text-muted-foreground'"
            >
              <svg v-if="step > n" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span v-else>{{ n }}</span>
            </span>
            <span
              class="text-[10px] font-medium uppercase tracking-wide transition-colors duration-300"
              :class="step === n ? 'text-primary' : step > n ? 'text-primary/60' : 'text-muted-foreground/60'"
            >{{ ['Búsqueda', 'Registro', 'Orden'][n - 1] }}</span>
          </div>
          <div
            v-if="n < 3"
            class="w-16 h-px mx-1 mb-5 transition-all duration-500"
            :class="step > n ? 'bg-primary/50' : 'bg-border'"
          />
        </template>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!-- STEP 1: Vehicle search                                              -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <div v-if="step === 1" class="space-y-4">
        <div class="space-y-1.5">
          <Label for="matricula-search">Matrícula del vehículo</Label>
          <div class="flex gap-2">
            <Input
              id="matricula-search"
              v-model="matriculaInput"
              placeholder="Ej. 1234ABC"
              class="uppercase"
              :disabled="searchLoading"
              @keydown="handleSearchKeydown"
            />
            <Button
              variant="secondary"
              :disabled="searchLoading || matriculaInput.trim().length < 6"
              @click="searchNow"
            >
              {{ searchLoading ? 'Buscando…' : 'Buscar' }}
            </Button>
          </div>
        </div>

        <!-- Search loading spinner -->
        <p v-if="searchLoading" class="text-sm text-muted-foreground animate-pulse">
          Buscando vehículo…
        </p>

        <!-- API error -->
        <div
          v-if="searchError"
          class="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2 text-sm text-destructive"
        >
          {{ searchError }}
        </div>

        <!-- Vehicle not found -->
        <div
          v-if="vehicleNotFound && !searchLoading"
          class="rounded-md bg-muted border border-border px-3 py-3 text-sm space-y-2"
        >
          <p class="font-medium">Vehículo no encontrado. ¿Crear nuevo?</p>
          <Button size="sm" @click="goToCreateNewVehicle">
            Registrar cliente y vehículo
          </Button>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!-- STEP 2: Create client + vehicle                                     -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <div v-else-if="step === 2" class="space-y-4">
        <!-- Client sub-form -->
        <fieldset class="space-y-3 border border-border rounded-md p-3">
          <legend class="px-1 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Datos del cliente
          </legend>

          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <Label for="c-nombre">Nombre <span class="text-destructive">*</span></Label>
              <Input id="c-nombre" v-model="clientForm.nombre" placeholder="Juan" :disabled="step2Loading" />
            </div>
            <div class="space-y-1">
              <Label for="c-apellido">Apellido <span class="text-destructive">*</span></Label>
              <Input id="c-apellido" v-model="clientForm.apellido" placeholder="García" :disabled="step2Loading" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <Label for="c-nif">NIF/DNI <span class="text-destructive">*</span></Label>
              <Input id="c-nif" v-model="clientForm.nif_dni" placeholder="12345678A" :disabled="step2Loading" />
            </div>
            <div class="space-y-1">
              <Label for="c-tel">Teléfono <span class="text-destructive">*</span></Label>
              <Input
                id="c-tel"
                v-model="clientForm.telefono"
                placeholder="612345678"
                inputmode="tel"
                :disabled="step2Loading"
                :class="telefonoError ? 'border-destructive focus-visible:ring-destructive/30' : ''"
                @blur="touch('telefono')"
                @input="touch('telefono')"
              />
              <p v-if="telefonoError" class="flex items-center gap-1 text-xs text-destructive mt-0.5">
                <svg class="w-3 h-3 shrink-0" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm.75 4.25a.75.75 0 0 0-1.5 0v3.5a.75.75 0 0 0 1.5 0v-3.5zm-.75 6a.875.875 0 1 0 0-1.75.875.875 0 0 0 0 1.75z"/></svg>
                {{ telefonoError }}
              </p>
            </div>
          </div>

          <div class="space-y-1">
            <Label for="c-email">Email <span class="text-muted-foreground text-xs">(opcional)</span></Label>
            <Input
              id="c-email"
              v-model="clientForm.email"
              type="email"
              placeholder="juan@ejemplo.com"
              :disabled="step2Loading"
              :class="emailError ? 'border-destructive focus-visible:ring-destructive/30' : ''"
              @blur="touch('email')"
              @input="touch('email')"
            />
            <p v-if="emailError" class="flex items-center gap-1 text-xs text-destructive mt-0.5">
              <svg class="w-3 h-3 shrink-0" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm.75 4.25a.75.75 0 0 0-1.5 0v3.5a.75.75 0 0 0 1.5 0v-3.5zm-.75 6a.875.875 0 1 0 0-1.75.875.875 0 0 0 0 1.75z"/></svg>
              {{ emailError }}
            </p>
          </div>

          <div class="space-y-1">
            <Label for="c-direccion">Dirección <span class="text-destructive">*</span></Label>
            <Input id="c-direccion" v-model="clientForm.direccion" placeholder="Calle Mayor 15, 2ºA" :disabled="step2Loading" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <Label for="c-localidad">Localidad <span class="text-destructive">*</span></Label>
              <Input id="c-localidad" v-model="clientForm.localidad" placeholder="Madrid" :disabled="step2Loading" />
            </div>
            <div class="space-y-1">
              <Label for="c-provincia">Provincia <span class="text-destructive">*</span></Label>
              <Input id="c-provincia" v-model="clientForm.provincia" placeholder="Madrid" :disabled="step2Loading" />
            </div>
          </div>
        </fieldset>

        <!-- Vehicle sub-form -->
        <fieldset class="space-y-3 border border-border rounded-md p-3">
          <legend class="px-1 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Datos del vehículo
          </legend>

          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <Label for="v-matricula">Matrícula <span class="text-destructive">*</span></Label>
              <Input id="v-matricula" v-model="vehicleForm.matricula" placeholder="1234ABC" class="uppercase" :disabled="step2Loading" />
            </div>
            <div class="space-y-1">
              <Label for="v-año">Año <span class="text-destructive">*</span></Label>
              <Input id="v-año" v-model="vehicleForm.año" type="number" inputmode="numeric" placeholder="2019" :disabled="step2Loading" @keydown="guardInt" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <Label for="v-marca">Marca <span class="text-destructive">*</span></Label>
              <Input id="v-marca" v-model="vehicleForm.marca" placeholder="Seat" :disabled="step2Loading" />
            </div>
            <div class="space-y-1">
              <Label for="v-modelo">Modelo <span class="text-destructive">*</span></Label>
              <Input id="v-modelo" v-model="vehicleForm.modelo" placeholder="León" :disabled="step2Loading" />
            </div>
          </div>
        </fieldset>

        <!-- Step 2 error -->
        <div
          v-if="step2Error"
          class="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2 text-sm text-destructive"
        >
          {{ step2Error }}
        </div>

        <DialogFooter class="gap-2 pt-1">
          <Button variant="ghost" :disabled="step2Loading" @click="step = 1">
            Volver
          </Button>
          <Button :disabled="step2Loading" @click="handleStep2Submit">
            {{ step2Loading ? 'Registrando…' : 'Continuar' }}
          </Button>
        </DialogFooter>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!-- STEP 3: Order description                                           -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <div v-else-if="step === 3" class="space-y-4">
        <!-- Found vehicle card -->
        <div
          v-if="foundVehicle"
          class="rounded-md border border-border bg-muted/30 px-3 py-2 text-sm space-y-1"
        >
          <p class="font-semibold">
            {{ foundVehicle.matricula }} — {{ foundVehicle.marca }} {{ foundVehicle.modelo }}
            <span class="text-muted-foreground font-normal">({{ foundVehicle['año'] }})</span>
          </p>
          <p class="text-muted-foreground">
            Cliente: {{ foundVehicle.cliente.apellido }}, {{ foundVehicle.cliente.nombre }}
          </p>
        </div>

        <!-- Newly created vehicle card -->
        <div
          v-else-if="createdVehicleId !== null"
          class="rounded-md border border-border bg-muted/30 px-3 py-2 text-sm space-y-1"
        >
          <p class="font-semibold">
            {{ vehicleForm.matricula }} — {{ vehicleForm.marca }} {{ vehicleForm.modelo }}
            <span class="text-muted-foreground font-normal">({{ vehicleForm.año }})</span>
          </p>
          <p class="text-muted-foreground" v-if="createdClienteData">
            Cliente: {{ createdClienteData.apellido }}, {{ createdClienteData.nombre }}
          </p>
        </div>

        <!-- descripcion -->
        <div class="space-y-1.5">
          <Label for="o-descripcion">
            Descripción de la avería <span class="text-destructive">*</span>
          </Label>
          <textarea
            id="o-descripcion"
            v-model="orderForm.descripcion"
            rows="3"
            placeholder="El motor hace un ruido extraño al arrancar en frío…"
            :disabled="step3Loading"
            class="w-full rounded-lg border border-input bg-transparent px-2.5 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring disabled:opacity-50 disabled:cursor-not-allowed resize-none"
          />
        </div>

        <!-- kilometraje -->
        <div class="space-y-1.5">
          <Label for="o-km">
            Kilometraje <span class="text-muted-foreground text-xs">(opcional)</span>
          </Label>
          <Input
            id="o-km"
            v-model="orderForm.kilometraje"
            type="number"
            inputmode="numeric"
            placeholder="85000"
            min="0"
            :disabled="step3Loading"
            @keydown="guardInt"
          />
        </div>

        <!-- notas_internas -->
        <div class="space-y-1.5">
          <Label for="o-notas">
            Notas internas <span class="text-muted-foreground text-xs">(opcional)</span>
          </Label>
          <textarea
            id="o-notas"
            v-model="orderForm.notas_internas"
            rows="2"
            placeholder="Revisar también el aceite porque el cliente mencionó consumo elevado…"
            :disabled="step3Loading"
            class="w-full rounded-lg border border-input bg-transparent px-2.5 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring disabled:opacity-50 disabled:cursor-not-allowed resize-none"
          />
        </div>

        <!-- Step 3 error -->
        <div
          v-if="step3Error"
          class="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2 text-sm text-destructive"
        >
          {{ step3Error }}
        </div>

        <DialogFooter class="gap-2 pt-1">
          <Button
            variant="ghost"
            :disabled="step3Loading"
            @click="() => { step = foundVehicle ? 1 : 2 }"
          >
            Volver
          </Button>
          <Button :disabled="step3Loading" @click="handleStep3Submit">
            {{ step3Loading ? 'Creando orden…' : 'Crear Orden' }}
          </Button>
        </DialogFooter>
      </div>

      <!-- Cancel / Close button always at top-right is provided by DialogContent -->
    </DialogContent>
  </Dialog>
</template>
