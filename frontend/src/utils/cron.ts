/**
 * Humanize a 5-field cron expression into plain English.
 * Covers the patterns realistically used for social posting schedules.
 * Returns the original string for anything it can't parse cleanly.
 *
 * Field order: minute hour dom month dow
 */

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatTime(minute: string, hour: string): string {
  const h = parseInt(hour)
  const m = parseInt(minute)
  const suffix = h < 12 ? 'AM' : 'PM'
  const h12 = h % 12 === 0 ? 12 : h % 12
  return m === 0 ? `${h12} ${suffix}` : `${h12}:${m.toString().padStart(2, '0')} ${suffix}`
}

function parseDow(dow: string): string {
  // Single digit
  if (/^\d$/.test(dow)) return DAYS[parseInt(dow)] ?? dow
  // Comma list: 1,3,5
  if (dow.includes(',')) {
    return dow.split(',').map(d => DAYS[parseInt(d)] ?? d).join(', ')
  }
  // Range: 1-5
  if (dow.includes('-')) {
    const [start, end] = dow.split('-').map(Number)
    if (start === 1 && end === 5) return 'Weekdays'
    if (start === 0 && end === 6) return 'Every day'
    return `${DAYS[start]}-${DAYS[end]}`
  }
  return dow
}

function parseMonth(month: string): string {
  if (/^\d+$/.test(month)) return MONTHS[parseInt(month) - 1] ?? month
  return month
}

export function humanizeCron(expr: string | null | undefined): string {
  if (!expr) return 'Manual'

  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return expr

  const [minute, hour, dom, month, dow] = parts

  const everyMinute = minute === '*'
  const everyHour = hour === '*'
  const everyDom = dom === '*'
  const everyMonth = month === '*'
  const everyDow = dow === '*'

  // Reject non-trivial step/range combos in time fields — fall back to raw
  if ((minute.includes('/') || minute.includes('-')) && minute !== '*') return expr
  if ((hour.includes('/') || hour.includes('-')) && hour !== '*') return expr

  // Every minute
  if (everyMinute && everyHour && everyDom && everyMonth && everyDow) return 'Every minute'

  // Every N minutes: */N * * * *
  if (minute.startsWith('*/') && everyHour && everyDom && everyMonth && everyDow) {
    const n = minute.slice(2)
    return `Every ${n} min`
  }

  // Hourly at :MM — 30 * * * *
  if (!everyMinute && everyHour && everyDom && everyMonth && everyDow) {
    return `Hourly at :${minute.padStart(2, '0')}`
  }

  // Every N hours: 0 */N * * *
  if (minute === '0' && hour.startsWith('*/') && everyDom && everyMonth && everyDow) {
    const n = hour.slice(2)
    return `Every ${n}h`
  }

  // Fixed time, specific dow(s), every month
  if (!everyMinute && !everyHour && everyDom && everyMonth && !everyDow) {
    const time = formatTime(minute, hour)
    const day = parseDow(dow)
    // Multiple days (comma)
    if (dow.includes(',')) return `${day} at ${time}`
    if (dow === '1-5') return `Weekdays at ${time}`
    return `${day}s at ${time}`
  }

  // Fixed time, every day
  if (!everyMinute && !everyHour && everyDom && everyMonth && everyDow) {
    return `Daily at ${formatTime(minute, hour)}`
  }

  // Fixed time, specific dom, every month, every dow
  if (!everyMinute && !everyHour && !everyDom && everyMonth && everyDow) {
    return `Monthly on the ${dom} at ${formatTime(minute, hour)}`
  }

  // Fixed time, specific month + dom
  if (!everyMinute && !everyHour && !everyDom && !everyMonth && everyDow) {
    return `${parseMonth(month)} ${dom} at ${formatTime(minute, hour)}`
  }

  // Fallback: return raw but trimmed
  return expr
}
