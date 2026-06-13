<script setup lang="ts">
import { computed } from 'vue'
import type { components } from '@/types/api'
import { Button } from '@/components/ui/button'

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

const isDisabled = computed(() => props.disabled || props.isLoading)

function updateField<K extends keyof BudgetItemFormValue>(key: K, value: BudgetItemFormValue[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
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
      @change="updateField('tipo', ($event.target as HTMLSelectElement).value as TipoItem)"
    >
      <option value="mano_obra">Mano de obra</option>
      <option value="pieza">Pieza</option>
    </select>

    <!-- cantidad -->
    <input
      class="h-8 w-20 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
      type="number"
      placeholder="Cant."
      min="0"
      step="0.01"
      :value="modelValue.cantidad"
      :disabled="isDisabled"
      @input="updateField('cantidad', parseFloat(($event.target as HTMLInputElement).value) || 0)"
    />

    <!-- precio_unitario -->
    <input
      class="h-8 w-24 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
      type="number"
      placeholder="P. Unit. €"
      min="0"
      step="0.01"
      :value="modelValue.precio_unitario"
      :disabled="isDisabled"
      @input="updateField('precio_unitario', parseFloat(($event.target as HTMLInputElement).value) || 0)"
    />

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
