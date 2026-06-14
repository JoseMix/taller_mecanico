import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from '@/lib/api'
import type { components } from '@/types/api'

type OrderResumen = components['schemas']['OrderResumen']
type Order = components['schemas']['Order']
type BudgetItem = components['schemas']['BudgetItem']
type BudgetItemCreate = components['schemas']['BudgetItemCreate']
type BudgetItemUpdate = components['schemas']['BudgetItemUpdate']
type EstadoOrden = components['schemas']['EstadoOrden']
type OrderCreate = components['schemas']['OrderCreate']
type OrderUpdate = components['schemas']['OrderUpdate']

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref<OrderResumen[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchOrders() {
    loading.value = true
    error.value = null
    try {
      orders.value = await apiGet<OrderResumen[]>('/ordenes')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Error desconocido'
    } finally {
      loading.value = false
    }
  }

  async function createOrder(data: OrderCreate) {
    const newOrder = await apiPost<Order>('/ordenes', data)
    await fetchOrders()
    return newOrder
  }

  async function updateEstado(orderId: number, nuevo_estado: EstadoOrden, items_cancelacion?: BudgetItemCreate[]) {
    await apiPatch<Order>(`/ordenes/${orderId}/estado`, { nuevo_estado, items_cancelacion })
    await fetchOrders()
  }

  async function updateOrden(orderId: number, data: OrderUpdate) {
    await apiPut<Order>(`/ordenes/${orderId}`, data)
    await fetchOrders()
  }

  async function deleteOrden(orderId: number) {
    await apiDelete(`/ordenes/${orderId}`)
    await fetchOrders()
  }

  async function addItem(orderId: number, item: BudgetItemCreate) {
    const result = await apiPost<BudgetItem>(`/ordenes/${orderId}/items`, item)
    await fetchOrders()
    return result
  }

  async function updateItem(orderId: number, itemId: number, item: BudgetItemUpdate) {
    await apiPut<BudgetItem>(`/ordenes/${orderId}/items/${itemId}`, item)
    await fetchOrders()
  }

  async function deleteItem(orderId: number, itemId: number) {
    await apiDelete(`/ordenes/${orderId}/items/${itemId}`)
    await fetchOrders()
  }

  return { orders, loading, error, fetchOrders, createOrder, updateEstado, updateOrden, deleteOrden, addItem, updateItem, deleteItem }
})
