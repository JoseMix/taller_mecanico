<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config.store'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { toast } from 'vue-sonner'
import { guardDecimal } from '@/lib/inputGuards'

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
      tarifa_hora: String(tarifa_hora.value ?? ''),
      nombre_taller: String(nombre_taller.value ?? ''),
      cif_taller: String(cif_taller.value ?? ''),
      direccion_taller: String(direccion_taller.value ?? ''),
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
  <div class="min-h-[calc(100vh-3.5rem)] py-12 px-6">
    <div class="max-w-2xl mx-auto space-y-8">

      <!-- ── Page header ─────────────────────────────────────────────────── -->
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center flex-shrink-0 mt-0.5">
          <svg class="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </div>
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-foreground font-mono uppercase">Configuración</h1>
          <p class="text-sm text-muted-foreground mt-1">Datos del taller y parámetros de facturación</p>
        </div>
      </div>

      <!-- ── Sección: Identidad del taller ──────────────────────────────── -->
      <section class="rounded-xl border border-border bg-card overflow-hidden">
        <div class="px-5 py-3.5 border-b border-border flex items-center gap-2.5">
          <span class="w-1.5 h-1.5 rounded-full bg-primary" />
          <h2 class="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Identidad del taller</h2>
        </div>
        <div class="p-5 space-y-4">
          <div class="space-y-1.5">
            <Label for="nombre_taller" class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Nombre del taller
            </Label>
            <Input
              id="nombre_taller"
              v-model="nombre_taller"
              placeholder="Taller García e Hijos"
              class="bg-background/50"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <Label for="cif_taller" class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                CIF
              </Label>
              <Input
                id="cif_taller"
                v-model="cif_taller"
                placeholder="B12345678"
                class="bg-background/50 font-mono"
              />
            </div>
            <div class="space-y-1.5">
              <Label for="direccion_taller" class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Dirección
              </Label>
              <Input
                id="direccion_taller"
                v-model="direccion_taller"
                placeholder="Calle Industria 42, Madrid"
                class="bg-background/50"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- ── Sección: Tarifas ────────────────────────────────────────────── -->
      <section class="rounded-xl border border-border bg-card overflow-hidden">
        <div class="px-5 py-3.5 border-b border-border flex items-center gap-2.5">
          <span class="w-1.5 h-1.5 rounded-full bg-primary" />
          <h2 class="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Tarifas de facturación</h2>
        </div>
        <div class="p-5">
          <div class="flex items-end gap-6">
            <div class="space-y-1.5 flex-1">
              <Label for="tarifa_hora" class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Tarifa por hora
              </Label>
              <div class="relative">
                <Input
                  id="tarifa_hora"
                  v-model="tarifa_hora"
                  type="number"
                  inputmode="decimal"
                  min="0"
                  step="0.5"
                  placeholder="45.00"
                  class="bg-background/50 font-mono pr-8"
                  @keydown="guardDecimal"
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground font-mono">€</span>
              </div>
            </div>
            <!-- Preview de la tarifa -->
            <div class="pb-0.5 text-right">
              <p class="text-3xl font-bold font-mono text-primary tabular-nums leading-none">
                {{ tarifa_hora || '0' }}
                <span class="text-lg font-normal text-muted-foreground">€/h</span>
              </p>
              <p class="text-xs text-muted-foreground mt-1">tarifa actual</p>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Acción guardar ─────────────────────────────────────────────── -->
      <div class="flex justify-end">
        <Button
          :disabled="saving"
          class="min-w-36 relative"
          @click="save"
        >
          <span v-if="!saving" class="flex items-center gap-2">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
              <polyline points="17 21 17 13 7 13 7 21"/>
              <polyline points="7 3 7 8 15 8"/>
            </svg>
            Guardar cambios
          </span>
          <span v-else class="flex items-center gap-2">
            <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
            Guardando…
          </span>
        </Button>
      </div>

    </div>
  </div>
</template>
