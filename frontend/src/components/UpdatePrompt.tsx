import { useEffect } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'
import { toast } from './toast'

/** Registers the service worker; offers to reload when a new version is ready. */
export function UpdatePrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    offlineReady: [offlineReady, setOfflineReady],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(_url, registration) {
      // Check for a new version every hour while the app stays open.
      if (registration) window.setInterval(() => void registration.update(), 60 * 60_000)
    },
  })

  useEffect(() => {
    if (offlineReady) {
      toast('The app is ready to work offline.', 'success')
      setOfflineReady(false)
    }
  }, [offlineReady, setOfflineReady])

  if (!needRefresh) return null
  return (
    <div className="update-bar" role="alert">
      <span>A new version is available.</span>
      <button className="btn btn-sm btn-primary" onClick={() => void updateServiceWorker(true)}>
        Reload
      </button>
      <button className="btn btn-sm" onClick={() => setNeedRefresh(false)}>
        Later
      </button>
    </div>
  )
}
