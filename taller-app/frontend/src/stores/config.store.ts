import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiGet, apiPut } from '@/lib/api'
import type { components } from '@/types/api'

type ConfigMap = components['schemas']['ConfigMap']

export const useConfigStore = defineStore('config', () => {
  const config = ref<ConfigMap>({})
  const loading = ref(false)

  async function fetchConfig() {
    loading.value = true
    try {
      config.value = await apiGet<ConfigMap>('/config')
    } finally {
      loading.value = false
    }
  }

  async function updateConfig(data: ConfigMap) {
    config.value = await apiPut<ConfigMap>('/config', data)
  }

  return { config, loading, fetchConfig, updateConfig }
})
