import { ref, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import type { components } from '@/types/api'
import { apiGet } from '@/lib/api'

type Cliente = components['schemas']['Cliente']
type VehicleConHistorial = components['schemas']['VehicleConHistorial']

export type SearchType = 'matricula' | 'nif_dni' | 'apellido'

const MATRICULA_RE = /^[0-9]{4}-?[A-Z]{3}$/i
const NIF_DNI_RE = /^[0-9]{7,8}[A-Z]$/i

export function useSearch() {
  const query = ref('')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const vehicleResult = ref<VehicleConHistorial | null>(null)
  const clienteResults = ref<Cliente[]>([])

  const searchType = computed<SearchType>(() => {
    const q = query.value.trim()
    if (MATRICULA_RE.test(q)) return 'matricula'
    if (NIF_DNI_RE.test(q)) return 'nif_dni'
    return 'apellido'
  })

  async function doSearch(q: string) {
    const trimmed = q.trim()
    if (!trimmed) {
      vehicleResult.value = null
      clienteResults.value = []
      error.value = null
      return
    }

    loading.value = true
    error.value = null
    vehicleResult.value = null
    clienteResults.value = []

    try {
      if (MATRICULA_RE.test(trimmed)) {
        vehicleResult.value = await apiGet<VehicleConHistorial>(
          `/vehiculos/buscar?matricula=${encodeURIComponent(trimmed)}`,
        )
      } else if (NIF_DNI_RE.test(trimmed)) {
        clienteResults.value = await apiGet<Cliente[]>(
          `/clientes/buscar?nif_dni=${encodeURIComponent(trimmed)}`,
        )
      } else {
        clienteResults.value = await apiGet<Cliente[]>(
          `/clientes/buscar?apellido=${encodeURIComponent(trimmed)}`,
        )
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.message.includes('404')) {
        // no results — leave arrays empty
      } else {
        error.value = e instanceof Error ? e.message : 'Error en la búsqueda'
      }
    } finally {
      loading.value = false
    }
  }

  const debouncedSearch = useDebounceFn(doSearch, 400)

  function onQueryChange(val: string) {
    query.value = val
    debouncedSearch(val)
  }

  function clear() {
    query.value = ''
    vehicleResult.value = null
    clienteResults.value = []
    error.value = null
  }

  return {
    query,
    searchType,
    loading,
    error,
    vehicleResult,
    clienteResults,
    onQueryChange,
    clear,
  }
}
