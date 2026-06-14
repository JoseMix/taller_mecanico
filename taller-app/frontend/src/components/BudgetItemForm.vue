<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import type { components } from '@/types/api'
import { Button } from '@/components/ui/button'
import { useConfigStore } from '@/stores/config.store'
import { guardInt, guardDecimal } from '@/lib/inputGuards'

type TipoItem = components['schemas']['TipoItem']

interface BudgetItemFormValue {
  concepto: string
  tipo: TipoItem
  cantidad: number
  precio_unitario: number
}

const props = withDefaults(defineProps<{
  modelValue: BudgetItemFormValue
  disabled?: boolean
  isLoading?: boolean
}>(), {
  disabled: false,
  isLoading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: BudgetItemFormValue]
  save: []
  cancel: []
}>()

const configStore = useConfigStore()

onMounted(async () => {
  if (!Object.keys(configStore.config).length) {
    await configStore.fetchConfig()
  }
})

const tarifaHora = computed(() => {
  const raw = configStore.config['tarifa_hora']
  return raw ? parseFloat(String(raw)) || 0 : 0
})

const isManoObra = computed(() => props.modelValue.tipo === 'mano_obra')
const isDisabled = computed(() => props.disabled || props.isLoading)

// Auto-sync precio_unitario → tarifaHora when tipo is mano_obra
watch(
  [() => props.modelValue.tipo, tarifaHora],
  ([tipo, tarifa]) => {
    if (tipo === 'mano_obra' && props.modelValue.precio_unitario !== tarifa) {
      emit('update:modelValue', { ...props.modelValue, precio_unitario: tarifa as number })
    }
  },
  { immediate: true },
)

function updateField<K extends keyof BudgetItemFormValue>(key: K, value: BudgetItemFormValue[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function handleTipoChange(tipo: TipoItem) {
  const precio_unitario = tipo === 'mano_obra' ? tarifaHora.value : 0
  emit('update:modelValue', { ...props.modelValue, tipo, precio_unitario })
}

function handleCantidad(raw: string) {
  // Always integer: floor negative-safe
  const n = parseInt(raw, 10)
  updateField('cantidad', isNaN(n) || n < 1 ? 1 : n)
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 rounded-md border border-dashed border-muted-foreground/40 bg-muted/30 p-2">

    <!-- concepto -->
    <input
      class="h-8 flex-1 min-w-[120px] rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
      type="text"
      placeholder="Concepto"
      :value="modelValue.concepto"
      :disabled="isDisabled"
      @input="updateField('concepto', ($event.target as HTMLInputElement).value)"
    />

    <!-- tipo -->
    <select
      class="h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
      :value="modelValue.tipo"
      :disabled="isDisabled"
      @change="handleTipoChange(($event.target as HTMLSelectElement).value as TipoItem)"
    >
      <option value="mano_obra">Mano de obra</option>
      <option value="pieza">Pieza</option>
    </select>

    <!-- cantidad — always integer -->
    <input
      class="h-8 w-20 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
      type="number"
      inputmode="numeric"
      :placeholder="isManoObra ? 'Horas' : 'Cant.'"
      min="1"
      step="1"
      :value="modelValue.cantidad"
      :disabled="isDisabled"
      @keydown="guardInt"
      @input="handleCantidad(($event.target as HTMLInputElement).value)"
    />

    <!-- mano_obra: tarifa display (read-only) -->
    <template v-if="isManoObra">
      <span
        v-if="tarifaHora > 0"
        class="h-8 flex items-center px-2 text-sm text-muted-foreground bg-muted rounded border border-border font-mono whitespace-nowrap"
      >
        {{ tarifaHora.toFixed(2) }} €/h
      </span>
      <span
        v-else
        class="h-8 flex items-center px-2 text-sm text-amber-500 bg-amber-50 dark:bg-amber-950/30 rounded border border-amber-200 dark:border-amber-800 whitespace-nowrap"
      >
        Sin tarifa — configura en Ajustes
      </span>
    </template>

    <!-- pieza: precio por unidad (editable) -->
    <template v-else>
      <input
        class="h-8 w-24 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed font-mono"
        type="number"
        inputmode="decimal"
        placeholder="€ / ud."
        min="0"
        step="0.01"
        :value="modelValue.precio_unitario"
        :disabled="isDisabled"
        @keydown="guardDecimal"
        @input="updateField('precio_unitario', parseFloat(($event.target as HTMLInputElement).value) || 0)"
      />
    </template>

    <!-- subtotal preview -->
    <span class="text-xs text-muted-foreground whitespace-nowrap font-mono">
      = {{ (modelValue.cantidad * modelValue.precio_unitario).toFixed(2) }} €
    </span>

    <!-- actions -->
    <div class="flex gap-1 shrink-0">
      <Button
        size="sm"
        :disabled="isDisabled"
        @click="emit('save')"
      >
        {{ isLoading ? 'Guardando…' : 'Guardar' }}
      </Button>
      <Button
        size="sm"
        variant="ghost"
        @click="emit('cancel')"
      >
        Cancelar
      </Button>
    </div>
  </div>
</template>
