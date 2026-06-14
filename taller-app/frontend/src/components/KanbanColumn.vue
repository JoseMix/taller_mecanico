<script setup lang="ts">
import type { components } from '@/types/api'
import OrderCard from './OrderCard.vue'

type OrderResumen = components['schemas']['OrderResumen']

const props = defineProps<{
  estado: string
  orders: OrderResumen[]
}>()

const emit = defineEmits<{
  'order-click': [order: OrderResumen]
}>()

const ESTADO_LABELS: Record<string, string> = {
  recibida: 'Recibida',
  presupuestado: 'Presupuestado',
  en_reparacion: 'En Reparación',
  finalizada: 'Finalizada',
  entregado: 'Entregado',
  rechazado: 'Rechazado',
}

// Indicador de color lateral por estado
const ESTADO_ACCENT: Record<string, string> = {
  recibida:      'bg-slate-500/50',
  presupuestado: 'bg-sky-500/60',
  en_reparacion: 'bg-primary',
  finalizada:    'bg-amber-400/70',
  entregado:     'bg-emerald-500/70',
  rechazado:     'bg-red-500/70',
}

const estadoLabel = (estado: string) => ESTADO_LABELS[estado] ?? estado
const accentClass = (estado: string) => ESTADO_ACCENT[estado] ?? 'bg-border'
</script>

<template>
  <div class="flex flex-col min-w-[220px] w-64 bg-card rounded-xl border border-border overflow-hidden">
    <!-- Column Header -->
    <div class="flex items-center justify-between px-3 py-2.5 border-b border-border bg-muted/30">
      <div class="flex items-center gap-2 min-w-0">
        <!-- Dot de color por estado -->
        <span :class="['flex-shrink-0 w-2 h-2 rounded-full', accentClass(estado)]" />
        <span class="font-semibold text-xs tracking-wide uppercase text-foreground truncate">
          {{ estadoLabel(estado) }}
        </span>
      </div>
      <!-- Contador de órdenes -->
      <span class="ml-2 inline-flex items-center justify-center rounded-full bg-muted/80 text-muted-foreground text-xs font-mono font-medium min-w-[20px] h-5 px-1.5 flex-shrink-0">
        {{ orders.length }}
      </span>
    </div>

    <!-- Orders list -->
    <div class="flex-1 overflow-y-auto p-2 space-y-2 min-h-[80px] max-h-[calc(100vh-180px)]">
      <OrderCard
        v-for="order in orders"
        :key="order.id"
        :order="order"
        @click="emit('order-click', order)"
      />
      <div v-if="orders.length === 0" class="text-center text-xs text-muted-foreground/60 py-8 select-none font-mono">
        — vacío —
      </div>
    </div>
  </div>
</template>
