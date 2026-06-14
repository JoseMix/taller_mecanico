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

// Clases optimizadas para fondo dark navy
const ESTADO_CLASSES: Record<string, string> = {
  recibida:      'bg-slate-500/15 text-slate-300 border border-slate-500/30',
  presupuestado: 'bg-sky-500/15 text-sky-300 border border-sky-500/35',
  en_reparacion: 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/45 font-semibold',
  finalizada:    'bg-amber-500/15 text-amber-300 border border-amber-400/35',
  entregado:     'bg-emerald-500/15 text-emerald-300 border border-emerald-500/35',
  rechazado:     'bg-red-500/15 text-red-400 border border-red-500/40',
}

const LOCKED_ESTADOS = ['en_reparacion', 'finalizada', 'entregado', 'rechazado']

const isLocked = computed(() => LOCKED_ESTADOS.includes(props.order.estado))

const estadoLabel = computed(() => ESTADO_LABELS[props.order.estado] ?? props.order.estado)
const estadoClass = computed(
  () => ESTADO_CLASSES[props.order.estado] ?? 'bg-gray-500/15 text-gray-400 border border-gray-500/30',
)

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
  const año = (v as Record<string, unknown>)['año'] as number | undefined
  return `${v.marca} ${v.modelo}${año ? ' ' + año : ''}`
})

const matricula = computed(() => props.order.vehiculo?.matricula ?? '')
const apellido = computed(() => props.order.vehiculo?.cliente?.apellido ?? '')
</script>

<template>
  <Card
    class="cursor-pointer select-none transition-all duration-200 hover:-translate-y-0.5 hover:ring-1 hover:ring-primary/40 hover:shadow-cyan-glow-sm"
    @click="emit('click', order)"
  >
    <CardHeader class="pb-1">
      <div class="flex items-center justify-between gap-2">
        <!-- Número de orden en Geist Mono -->
        <span class="font-mono font-bold text-sm tracking-tight text-foreground">
          {{ order.numero_orden }}
        </span>
        <div class="flex items-center gap-1.5">
          <!-- Icono candado discreto -->
          <svg
            v-if="isLocked"
            class="w-3 h-3 text-muted-foreground flex-shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            title="Orden bloqueada"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          <!-- Badge de estado -->
          <span
            :class="['inline-flex items-center rounded-full px-2 py-0.5 text-xs', estadoClass]"
          >
            {{ estadoLabel }}
          </span>
        </div>
      </div>
    </CardHeader>
    <CardContent class="pt-0 space-y-1.5">
      <!-- Matrícula — destacada en Geist Mono -->
      <div v-if="matricula" class="flex items-center gap-2">
        <span class="font-mono font-bold text-xs tracking-widest uppercase text-primary/90">
          {{ matricula }}
        </span>
        <span class="text-xs text-muted-foreground truncate">{{ vehicleInfo }}</span>
      </div>
      <div v-if="apellido" class="text-xs text-muted-foreground">
        Cliente: <span class="font-medium text-foreground">{{ apellido }}</span>
      </div>
      <!-- Total — alineado a la derecha, con color sutil -->
      <div class="text-xs font-mono font-medium text-right text-muted-foreground pt-0.5">
        {{ budgetFormatted }}
      </div>
    </CardContent>
  </Card>
</template>
