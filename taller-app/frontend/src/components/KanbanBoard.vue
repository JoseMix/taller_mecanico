<script setup lang="ts">
import { computed } from 'vue'
import type { components } from '@/types/api'
import { useOrdersStore } from '@/stores/orders.store'
import KanbanColumn from './KanbanColumn.vue'

type OrderResumen = components['schemas']['OrderResumen']

const emit = defineEmits<{
  'order-click': [order: OrderResumen]
}>()

const ordersStore = useOrdersStore()

const ESTADOS = ['recibida', 'presupuestado', 'en_reparacion', 'finalizada', 'entregado', 'rechazado']

const ordersByEstado = computed(() => {
  const map: Record<string, OrderResumen[]> = {}
  for (const estado of ESTADOS) {
    map[estado] = []
  }
  for (const order of ordersStore.orders) {
    if (map[order.estado]) {
      map[order.estado].push(order)
    }
  }
  return map
})
</script>

<template>
  <div class="flex gap-3 overflow-x-auto pb-4 h-full">
    <KanbanColumn
      v-for="estado in ESTADOS"
      :key="estado"
      :estado="estado"
      :orders="ordersByEstado[estado]"
      @order-click="emit('order-click', $event)"
    />
  </div>
</template>
