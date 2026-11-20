import { useEffect, useState, useSyncExternalStore } from 'react'
import { dismiss, getToasts, subscribeToasts, type ToastItem } from './toast'

export function Toaster() {
  const items = useSyncExternalStore(subscribeToasts, getToasts)
  return (
    <div className="toasts" role="status" aria-live="polite">
      {items.map((t) => (
        <ToastView key={t.id} item={t} />
      ))}
    </div>
  )
}

function ToastView({ item }: { item: ToastItem }) {
  const [shown, setShown] = useState(false)
  useEffect(() => {
    const frame = requestAnimationFrame(() => setShown(true))
    return () => cancelAnimationFrame(frame)
  }, [])
  return (
    <div className={`toast toast-${item.kind}${shown ? ' shown' : ''}`}>
      <span>{item.message}</span>
      {item.action && (
        <button
          className="btn btn-sm btn-light"
          onClick={() => {
            item.action!.run()
            dismiss(item.id)
          }}
        >
          {item.action.label}
        </button>
      )}
    </div>
  )
}
