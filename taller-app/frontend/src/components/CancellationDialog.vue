<script setup lang="ts">
import { ref, computed } from 'vue'
import type { components } from '@/types/api'
import { useOrdersStore } from '@/stores/orders.store'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

type TipoItem = components['schemas']['TipoItem']
type BudgetItemCreate = components['schemas']['BudgetItemCreate']

interface LineaItem {
  concepto: string
  tipo: TipoItem
  cantidad: number
  precio_unitario: number
}

const props = defineProps<{
  open: boolean
  orderId: number
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirmed: []
}>()

const ordersStore = useOrdersStore()
const isLoading = ref(false)
const errorMsg = ref<string | null>(null)

function emptyLine(): LineaItem {
  return { concepto: '', tipo: 'mano_obra', cantidad: 1, precio_unitario: 0 }
}

const lines = ref<LineaItem[]>([emptyLine()])

function addLine() {
  lines.value.push(emptyLine())
}

function removeLine(index: number) {
  lines.value.splice(index, 1)
}

const subtotal = computed(() =>
  lines.value.reduce((sum, l) => sum + l.cantidad * l.precio_unitario, 0),
)

function formatCurrency(val: number) {
  return val.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €'
}

async function handleConfirm() {
  errorMsg.value = null
  isLoading.value = true
  try {
    const items: BudgetItemCreate[] = lines.value.map((l) => ({
      concepto: l.concepto,
      tipo: l.tipo,
      cantidad: l.cantidad,
      precio_unitario: l.precio_unitario,
      es_cargo_cancelacion: true,
    }))
    await ordersStore.updateEstado(props.orderId, 'rechazado', items)
    emit('update:open', false)
    emit('confirmed')
    // reset lines for next use
    lines.value = [emptyLine()]
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : 'Error al cancelar la reparación'
  } finally {
    isLoading.value = false
  }
}

function handleClose() {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle>Cancelar reparación</DialogTitle>
        <DialogDescription>
          Introduce los trabajos realizados y materiales usados para el cobro
        </DialogDescription>
      </DialogHeader>

      <!-- Error -->
      <div v-if="errorMsg" class="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2 text-sm text-destructive">
        {{ errorMsg }}
      </div>

      <!-- Items list -->
      <div class="space-y-2 max-h-72 overflow-y-auto pr-1">
        <div
          v-for="(line, index) in lines"
          :key="index"
          class="flex flex-wrap items-center gap-2 rounded-md border border-border bg-muted/20 p-2"
        >
          <!-- concepto -->
          <input
            v-model="line.concepto"
            class="h-8 flex-1 min-w-[120px] rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            type="text"
            placeholder="Concepto"
            :disabled="isLoading"
          />

          <!-- tipo -->
          <select
            v-model="line.tipo"
            class="h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            :disabled="isLoading"
          >
            <option value="mano_obra">Mano de obra</option>
            <option value="pieza">Pieza</option>
          </select>

          <!-- cantidad -->
          <input
            v-model.number="line.cantidad"
            class="h-8 w-20 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            type="number"
            placeholder="Cant."
            min="0"
            step="0.01"
            :disabled="isLoading"
          />

          <!-- precio_unitario -->
          <input
            v-model.number="line.precio_unitario"
            class="h-8 w-24 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            type="number"
            placeholder="P. Unit. €"
            min="0"
            step="0.01"
            :disabled="isLoading"
          />

          <!-- remove row (only if more than one) -->
          <button
            v-if="lines.length > 1"
            type="button"
            class="text-muted-foreground hover:text-destructive text-sm px-1"
            :disabled="isLoading"
            @click="removeLine(index)"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Add line -->
      <Button variant="outline" size="sm" :disabled="isLoading" @click="addLine">
        + Añadir línea
      </Button>

      <!-- Subtotal -->
      <div class="flex justify-end text-sm font-semibold pt-1">
        Subtotal: {{ formatCurrency(subtotal) }}
      </div>

      <DialogFooter class="gap-2 pt-2">
        <Button variant="ghost" :disabled="isLoading" @click="handleClose">
          Volver
        </Button>
        <Button variant="destructive" :disabled="isLoading" @click="handleConfirm">
          {{ isLoading ? 'Procesando…' : 'Confirmar cancelación' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
