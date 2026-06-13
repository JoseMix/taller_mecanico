<script setup lang="ts">
import { computed } from 'vue'
import type { components } from '@/types/api'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

type OrderResumen = components['schemas']['OrderResumen']

const props = defineProps<{
  order: OrderResumen
}>()

const emit = defineEmits<{
  click: [order: OrderResumen]
}>()

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

const LOCKED_ESTADOS = ['en_reparacion', 'finalizada', 'entregado', 'rechazado']

const isLocked = computed(() => LOCKED_ESTADOS.includes(props.order.estado))

const estadoLabel = computed(() => ESTADO_LABELS[props.order.estado] ?? props.order.estado)
const estadoClass = computed(
  () => ESTADO_CLASSES[props.order.estado] ?? 'bg-gray-100 text-gray-700 border-gray-300',
)

// OrderResumen exposes `total` (server-computed). Display it if present.
const budgetFormatted = computed(() => {
  const total = props.order.total ?? 0
  return total.toLocaleString('es-ES', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + ' €'
})

const vehicleInfo = computed(() => {
  const v = props.order.vehiculo
  if (!v) return ''
  // año is encoded as "año" in the type (año)
  const año = (v as Record<string, unknown>)['año'] as number | undefined
  return `${v.marca} ${v.modelo}${año ? ' ' + año : ''}`
})

const matricula = computed(() => props.order.vehiculo?.matricula ?? '')
const apellido = computed(() => props.order.vehiculo?.cliente?.apellido ?? '')
</script>

<template>
  <Card
    class="cursor-pointer hover:ring-2 hover:ring-primary/40 transition-all select-none"
    @click="emit('click', order)"
  >
    <CardHeader class="pb-1">
      <div class="flex items-center justify-between gap-2">
        <span class="font-mono font-bold text-base tracking-tight">{{ order.numero_orden }}</span>
        <div class="flex items-center gap-1">
          <span v-if="isLocked" class="text-sm" title="Orden bloqueada">🔒</span>
          <span
            :class="['inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium', estadoClass]"
          >
            {{ estadoLabel }}
          </span>
        </div>
      </div>
    </CardHeader>
    <CardContent class="pt-0 space-y-1">
      <div v-if="matricula" class="flex items-center gap-2">
        <span class="font-bold text-sm">{{ matricula }}</span>
        <span class="text-xs text-muted-foreground">{{ vehicleInfo }}</span>
      </div>
      <div v-if="apellido" class="text-xs text-muted-foreground">
        Cliente: <span class="font-medium text-foreground">{{ apellido }}</span>
      </div>
      <div class="text-xs font-medium text-right pt-1">
        {{ budgetFormatted }}
      </div>
    </CardContent>
  </Card>
</template>
