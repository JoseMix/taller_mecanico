import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { usePolling } from './usePolling'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

describe('usePolling', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('calls fn immediately on mount', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const TestComponent = defineComponent({
      setup() { usePolling(fn, 1000) },
      template: '<div />'
    })
    mount(TestComponent)
    // Flush microtasks so the async run() resolves
    await Promise.resolve()
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('calls fn again after interval', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const TestComponent = defineComponent({
      setup() { usePolling(fn, 1000) },
      template: '<div />'
    })
    mount(TestComponent)
    await Promise.resolve()
    vi.advanceTimersByTime(1000)
    await Promise.resolve()
    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('clears interval on unmount', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const TestComponent = defineComponent({
      setup() { usePolling(fn, 1000) },
      template: '<div />'
    })
    const wrapper = mount(TestComponent)
    await Promise.resolve()
    wrapper.unmount()
    vi.advanceTimersByTime(2000)
    await Promise.resolve()
    // fn was called once on mount, not again after unmount
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
