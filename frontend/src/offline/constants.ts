// Shared by the app and the service worker.

/** Cache Storage bucket holding files the user downloaded for offline use. The
 * service worker answers /media/ requests from it before trying the network. */
export const FILES_CACHE = 'studyplan-files-v1'
