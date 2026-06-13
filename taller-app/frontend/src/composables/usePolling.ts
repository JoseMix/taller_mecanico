import { onMounted, onUnmounted } from 'vue'

export function usePolling(fn: () => Promise<void> | void, intervalMs = 30_000) {
  let timer: ReturnType<typeof setInterval> | null = null

  async function run() {
    await fn()
  }

  function start() {
    run()
    timer = setInterval(run, intervalMs)
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
  }

  onMounted(start)
  onUnmounted(stop)

  return { start, stop }
}
