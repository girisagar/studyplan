import { useSyncExternalStore } from 'react'

function subscribe(listener: () => void) {
  window.addEventListener('online', listener)
  window.addEventListener('offline', listener)
  return () => {
    window.removeEventListener('online', listener)
    window.removeEventListener('offline', listener)
  }
}

export const isOnline = () => navigator.onLine

/** navigator.onLine: false means definitely offline; true may still fail. */
export function useOnline() {
  return useSyncExternalStore(subscribe, isOnline)
}
