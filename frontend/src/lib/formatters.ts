/**
 * Shared formatting utilities for the application
 */

/**
 * Format a number or string as USD currency
 */
export function formatCurrency(amount: string | number): string {
  const num = typeof amount === "string" ? Number.parseFloat(amount) : amount
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num)
}

/**
 * Format minutes as hours and minutes (e.g., "2h 30m")
 */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours === 0) return `${mins}m`
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}m`
}

/**
 * Format a date string as a short date (e.g., "Jan 15, 2024")
 */
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

/**
 * Format a date string as a date and time (e.g., "Jan 15, 2024, 2:30 PM")
 */
export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

/**
 * Format a date string as just time (e.g., "2:30 PM")
 */
export function formatTime(dateString: string): string {
  return new Date(dateString).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  })
}

/**
 * Truncate a string to a maximum length with ellipsis
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return `${str.slice(0, maxLength)}...`
}

/**
 * Validate a UUID string format
 */
export function isValidUUID(str: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(str)
}

/**
 * Parse comma-separated IDs and validate them as UUIDs
 */
export function parseAndValidateIds(idsString: string | undefined): string[] {
  if (!idsString) return []

  const ids = idsString.split(",").map((id) => id.trim()).filter(Boolean)

  // Filter out invalid UUIDs
  return ids.filter(isValidUUID)
}
