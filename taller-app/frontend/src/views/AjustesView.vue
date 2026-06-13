<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config.store'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { toast } from 'vue-sonner'

const configStore = useConfigStore()

const tarifa_hora = ref('')
const nombre_taller = ref('')
const cif_taller = ref('')
const direccion_taller = ref('')
const saving = ref(false)

onMounted(async () => {
  await configStore.fetchConfig()
  tarifa_hora.value = configStore.config['tarifa_hora'] ?? ''
  nombre_taller.value = configStore.config['nombre_taller'] ?? ''
  cif_taller.value = configStore.config['cif_taller'] ?? ''
  direccion_taller.value = configStore.config['direccion_taller'] ?? ''
})

async function save() {
  saving.value = true
  try {
    await configStore.updateConfig({
      tarifa_hora: tarifa_hora.value,
      nombre_taller: nombre_taller.value,
      cif_taller: cif_taller.value,
      direccion_taller: direccion_taller.value,
    })
    toast.success('Ajustes guardados')
  } catch (e: unknown) {
    toast.error(e instanceof Error ? e.message : 'Error al guardar')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-lg">
    <h1 class="text-2xl font-bold mb-6">Ajustes del taller</h1>

    <div class="space-y-5">
      <div class="space-y-1.5">
        <Label for="tarifa_hora">Tarifa por hora (€)</Label>
        <Input id="tarifa_hora" v-model="tarifa_hora" type="number" min="0" step="0.5" />
      </div>

      <div class="space-y-1.5">
        <Label for="nombre_taller">Nombre del taller</Label>
        <Input id="nombre_taller" v-model="nombre_taller" />
      </div>

      <div class="space-y-1.5">
        <Label for="cif_taller">CIF del taller</Label>
        <Input id="cif_taller" v-model="cif_taller" />
      </div>

      <div class="space-y-1.5">
        <Label for="direccion_taller">Dirección</Label>
        <Input id="direccion_taller" v-model="direccion_taller" />
      </div>

      <Button :disabled="saving" @click="save">
        {{ saving ? 'Guardando…' : 'Guardar cambios' }}
      </Button>
    </div>
  </div>
</template>
