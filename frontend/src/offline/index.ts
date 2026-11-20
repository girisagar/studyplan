import { hydrateCache } from './cache'
import { hydrateFiles } from './files'
import { hydrateOutbox } from './progress'
import { startSync } from './sync'

/** Load offline data into memory (before the first render), then start syncing. */
export async function startOffline() {
  try {
    await Promise.all([hydrateCache(), hydrateOutbox(), hydrateFiles()])
  } catch (error) {
    // IndexedDB unavailable (e.g. some private modes): run online-only.
    console.warn('Offline storage unavailable', error)
  }
  startSync()
}
