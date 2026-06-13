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

const estadoLabel = (estado: string) => ESTADO_LABELS[estado] ?? estado
</script>

<template>
  <div class="flex flex-col min-w-[220px] w-64 bg-muted/40 rounded-xl border border-border">
    <!-- Column Header -->
    <div class="flex items-center justify-between px-3 py-2 border-b border-border">
      <span class="font-semibold text-sm text-foreground truncate">{{ estadoLabel(estado) }}</span>
      <span class="ml-2 inline-flex items-center justify-center rounded-full bg-muted text-muted-foreground text-xs font-medium min-w-[20px] h-5 px-1.5">
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
      <div v-if="orders.length === 0" class="text-center text-xs text-muted-foreground py-6 select-none">
        Sin órdenes
      </div>
    </div>
  </div>
</template>
