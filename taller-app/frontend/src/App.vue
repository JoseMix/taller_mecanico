<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { Toaster } from '@/components/ui/sonner'
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <!-- Top Navbar — grafito oscuro con borde cyan inferior sutil -->
    <nav class="bg-[hsl(220_35%_7%)] border-b border-border shadow-lg shadow-black/40 relative">
      <!-- Línea de acento cyan en la parte inferior -->
      <div class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14">
          <!-- Logotipo / nombre app -->
          <div class="flex items-center gap-2.5">
            <!-- Icono: llave inglesa en cyan -->
            <div class="w-7 h-7 rounded-md bg-primary/15 border border-primary/30 flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
              </svg>
            </div>
            <span class="text-sm font-bold tracking-widest uppercase text-foreground font-mono">
              Taller<span class="text-primary">Gest</span>
            </span>
          </div>

          <!-- Navigation links -->
          <div class="flex items-center gap-1">
            <RouterLink
              to="/"
              class="relative px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-white/5"
              active-class="!text-primary nav-link-active"
            >
              Kanban
            </RouterLink>
            <RouterLink
              to="/buscar"
              class="relative px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-white/5"
              active-class="!text-primary nav-link-active"
            >
              Buscar
            </RouterLink>
            <RouterLink
              to="/ajustes"
              class="relative px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-white/5"
              active-class="!text-primary nav-link-active"
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
  <Toaster position="bottom-right" rich-colors />
</template>

<style scoped>
/* El link activo lleva un underline cyan como en el mockup */
:deep(.nav-link-active)::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: hsl(var(--primary));
  border-radius: 1px;
}
</style>
