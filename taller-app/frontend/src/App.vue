<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col">
    <!-- Top Navbar -->
    <nav class="bg-gray-900 text-white shadow-md">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14">
          <!-- App name -->
          <span class="text-lg font-bold tracking-wide text-white">TallerGest</span>

          <!-- Navigation links -->
          <div class="flex items-center gap-6">
            <RouterLink
              to="/"
              class="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              active-class="text-white border-b-2 border-blue-400 pb-0.5"
            >
              Kanban
            </RouterLink>
            <RouterLink
              to="/buscar"
              class="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              active-class="text-white border-b-2 border-blue-400 pb-0.5"
            >
              Buscar
            </RouterLink>
            <RouterLink
              to="/ajustes"
              class="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              active-class="text-white border-b-2 border-blue-400 pb-0.5"
            >
              Ajustes
            </RouterLink>
          </div>
        </div>
      </div>
    </nav>

    <!-- Page content -->
    <main class="flex-1">
      <RouterView />
    </main>
  </div>
</template>
