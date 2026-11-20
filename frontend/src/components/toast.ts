export type ToastKind = 'info' | 'success' | 'error'
export interface ToastItem {
  id: number
  message: string
  kind: ToastKind
  action?: { label: string; run: () => void }
}

let toasts: ToastItem[] = []
let nextId = 1
const listeners = new Set<() => void>()
const emit = () => listeners.forEach((l) => l())

export function toast(message: string, kind: ToastKind = 'info', action?: ToastItem['action']) {
  const id = nextId++
  toasts = [...toasts, { id, message, kind, action }]
  emit()
  window.setTimeout(() => dismiss(id), action ? 10_000 : 4_000)
  return id
}

export function dismiss(id: number) {
  toasts = toasts.filter((t) => t.id !== id)
  emit()
}

export function subscribeToasts(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export const getToasts = () => toasts
