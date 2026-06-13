<script setup lang="ts">
import { ref } from 'vue'
import type { components } from '@/types/api'
import { useOrdersStore } from '@/stores/orders.store'
import { usePolling } from '@/composables/usePolling'
import KanbanBoard from '@/components/KanbanBoard.vue'
import OrderDetailSheet from '@/components/OrderDetailSheet.vue'
import { Button } from '@/components/ui/button'

type OrderResumen = components['schemas']['OrderResumen']

const ordersStore = useOrdersStore()

// Polling: fetch orders every 30 seconds
usePolling(() => ordersStore.fetchOrders(), 30_000)

// Placeholder: NewOrderDialog will be implemented in Task 26
const showNewOrderDialog = ref(false)

// Selected order for OrderDetailSheet
const selectedOrder = ref<OrderResumen | null>(null)
const sheetOpen = ref(false)

function handleOrderClick(order: OrderResumen) {
  selectedOrder.value = order
  sheetOpen.value = true
}

function handleSheetClose() {
  sheetOpen.value = false
  selectedOrder.value = null
}
</script>

<template>
  <div class="flex flex-col h-full gap-4 p-4">
    <!-- Toolbar -->
    <div class="flex items-center justify-between shrink-0">
      <h1 class="text-xl font-bold">Tablero de Órdenes</h1>
      <Button @click="showNewOrderDialog = true">
        Nueva Orden
      </Button>
    </div>

    <!-- Loading state -->
    <div v-if="ordersStore.loading && ordersStore.orders.length === 0" class="flex-1 flex items-center justify-center">
      <span class="text-muted-foreground text-sm animate-pulse">Cargando órdenes…</span>
    </div>

    <!-- Kanban Board -->
    <div v-else class="flex-1 overflow-hidden">
      <KanbanBoard @order-click="handleOrderClick" />
    </div>

    <!-- Placeholder: NewOrderDialog (Task 26) -->
    <!-- <NewOrderDialog v-model:open="showNewOrderDialog" /> -->

    <!-- OrderDetailSheet -->
    <OrderDetailSheet
      v-model:open="sheetOpen"
      :order="selectedOrder"
      @close="handleSheetClose"
    />
  </div>
</template>
