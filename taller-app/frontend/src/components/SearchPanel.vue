<script setup lang="ts">
import { computed } from 'vue'
import type { components } from '@/types/api'
import { useSearch } from '@/composables/useSearch'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

type VehicleConHistorial = components['schemas']['VehicleConHistorial']
type OrderResumen = components['schemas']['OrderResumen']

const {
  query,
  searchType,
  loading,
  error,
  vehicleResult,
  clienteResults,
  onQueryChange,
  clear,
} = useSearch()

const TYPE_LABELS: Record<string, string> = {
  matricula: 'Matrícula',
  nif_dni: 'DNI / NIF',
  apellido: 'Apellido',
}

const TYPE_VARIANTS: Record<string, 'default' | 'secondary' | 'outline'> = {
  matricula: 'default',
  nif_dni: 'secondary',
  apellido: 'outline',
}

const ESTADO_LABELS: Record<string, string> = {
  recibida: 'Recibida',
  presupuestado: 'Presupuestado',
  en_reparacion: 'En Reparación',
  finalizada: 'Finalizada',
  entregado: 'Entregado',
  rechazado: 'Rechazado',
}

const ESTADO_CLASSES: Record<string, string> = {
  recibida: 'bg-slate-100 text-slate-700 border-slate-300',
  presupuestado: 'bg-blue-100 text-blue-700 border-blue-300',
  en_reparacion: 'bg-violet-100 text-violet-700 border-violet-300',
  finalizada: 'bg-amber-100 text-amber-700 border-amber-300',
  entregado: 'bg-green-100 text-green-700 border-green-300',
  rechazado: 'bg-red-100 text-red-700 border-red-300',
}

const hasResults = computed(
  () => vehicleResult.value !== null || clienteResults.value.length > 0,
)

const noResults = computed(
  () =>
    !loading.value &&
    !error.value &&
    query.value.trim().length > 0 &&
    !hasResults.value,
)

function vehicleYear(v: VehicleConHistorial): number | undefined {
  return (v as Record<string, unknown>)['año'] as number | undefined
}

function orderEstadoClass(order: OrderResumen) {
  return ESTADO_CLASSES[order.estado] ?? 'bg-gray-100 text-gray-700 border-gray-300'
}

function orderEstadoLabel(order: OrderResumen) {
  return ESTADO_LABELS[order.estado] ?? order.estado
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-4">
    <!-- Search input row -->
    <div class="flex items-center gap-2">
      <div class="relative flex-1">
        <Input
          :value="query"
          placeholder="Buscar por matrícula, DNI/NIF o apellido…"
          class="pr-8"
          @input="onQueryChange(($event.target as HTMLInputElement).value)"
        />
        <button
          v-if="query.length > 0"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Borrar búsqueda"
          @click="clear"
        >
          ✕
        </button>
      </div>
      <Badge v-if="query.trim().length > 0" :variant="TYPE_VARIANTS[searchType]">
        {{ TYPE_LABELS[searchType] }}
      </Badge>
    </div>

    <!-- Loading -->
    <p v-if="loading" class="text-sm text-muted-foreground text-center py-4">Buscando…</p>

    <!-- Error -->
    <p v-else-if="error" class="text-sm text-destructive text-center py-4">{{ error }}</p>

    <!-- No results -->
    <p v-else-if="noResults" class="text-sm text-muted-foreground text-center py-4">
      Sin resultados para "{{ query }}"
    </p>

    <!-- Vehicle result (matricula search) -->
    <Card v-else-if="vehicleResult" class="overflow-hidden">
      <CardHeader class="pb-2">
        <div class="flex items-center justify-between">
          <span class="font-bold text-lg font-mono tracking-widest">
            {{ vehicleResult.matricula }}
          </span>
          <span class="text-sm text-muted-foreground">
            {{ vehicleResult.marca }} {{ vehicleResult.modelo }}
            <span v-if="vehicleYear(vehicleResult)"> {{ vehicleYear(vehicleResult) }}</span>
          </span>
        </div>
        <div class="text-sm text-muted-foreground">
          Cliente:
          <span class="font-medium text-foreground">
            {{ vehicleResult.cliente.nombre }} {{ vehicleResult.cliente.apellido }}
          </span>
          <span v-if="vehicleResult.cliente.telefono" class="ml-2">
            · {{ vehicleResult.cliente.telefono }}
          </span>
        </div>
      </CardHeader>
      <CardContent class="pt-0">
        <p class="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
          Historial de órdenes ({{ vehicleResult.ordenes.length }})
        </p>
        <div v-if="vehicleResult.ordenes.length === 0" class="text-sm text-muted-foreground">
          Sin órdenes registradas
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="order in vehicleResult.ordenes"
            :key="order.id"
            class="flex items-center justify-between rounded border px-3 py-2 text-sm"
          >
            <span class="font-mono font-bold">{{ order.numero_orden }}</span>
            <span class="text-muted-foreground truncate max-w-[180px] mx-2">
              {{ order.descripcion }}
            </span>
            <span
              :class="[
                'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
                orderEstadoClass(order),
              ]"
            >
              {{ orderEstadoLabel(order) }}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Client list (apellido / nif_dni search) -->
    <div v-else-if="clienteResults.length > 0" class="space-y-2">
      <Card
        v-for="cliente in clienteResults"
        :key="cliente.id"
        class="overflow-hidden"
      >
        <CardContent class="pt-4 pb-4">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="font-semibold">{{ cliente.nombre }} {{ cliente.apellido }}</p>
              <p class="text-sm text-muted-foreground">{{ cliente.nif_dni }}</p>
            </div>
            <div class="text-right text-sm text-muted-foreground shrink-0">
              <p v-if="cliente.telefono">{{ cliente.telefono }}</p>
              <p v-if="cliente.email" class="truncate max-w-[180px]">{{ cliente.email }}</p>
            </div>
          </div>
          <div v-if="cliente.localidad || cliente.provincia" class="mt-1 text-xs text-muted-foreground">
            {{ [cliente.localidad, cliente.provincia].filter(Boolean).join(', ') }}
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
