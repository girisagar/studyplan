export function plural(n: number, one: string, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit++
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${units[unit]}`
}

export function formatDate(value: string | Date) {
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function timeAgo(value: string | number | Date) {
  const seconds = Math.round((Date.now() - new Date(value).getTime()) / 1000)
  const format = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
  if (seconds < 45) return 'just now'
  if (seconds < 3600) return format.format(-Math.round(seconds / 60), 'minute')
  if (seconds < 86_400) return format.format(-Math.round(seconds / 3600), 'hour')
  if (seconds < 30 * 86_400) return format.format(-Math.round(seconds / 86_400), 'day')
  return formatDate(new Date(value))
}

export function greeting(date = new Date()) {
  const hour = date.getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

export const PACE_LABEL = {
  ahead: 'Ahead of schedule',
  on_track: 'On track',
  behind: 'Behind schedule',
  done: 'Finished',
} as const
