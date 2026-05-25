import { ref } from 'vue'

export type ToastType = 'error' | 'success' | 'info'

export interface Toast {
  id: number
  type: ToastType
  message: string
}

let _nextId = 1
const toasts = ref<Toast[]>([])

export function useToast() {
  function show(message: string, type: ToastType = 'info', durationMs = 4000) {
    const id = _nextId++
    toasts.value = [...toasts.value, { id, type, message }]
    setTimeout(() => dismiss(id), durationMs)
  }

  function dismiss(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const error = (msg: string) => show(msg, 'error', 6000)
  const success = (msg: string) => show(msg, 'success', 3000)
  const info = (msg: string) => show(msg, 'info', 4000)

  return { toasts, show, dismiss, error, success, info }
}
