const NAVIGATION_KEYS = new Set([
  'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
  'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
  'Home', 'End',
])

/** Blocks every key that isn't a digit. Use on integer inputs. */
export function guardInt(e: KeyboardEvent) {
  if (NAVIGATION_KEYS.has(e.key) || e.ctrlKey || e.metaKey) return
  if (!/^\d$/.test(e.key)) e.preventDefault()
}

/** Blocks every key that isn't a digit or a single decimal point. Use on decimal inputs. */
export function guardDecimal(e: KeyboardEvent) {
  if (NAVIGATION_KEYS.has(e.key) || e.ctrlKey || e.metaKey) return
  if (e.key === '.') return // browser already prevents a second dot in type="number"
  if (!/^\d$/.test(e.key)) e.preventDefault()
}
