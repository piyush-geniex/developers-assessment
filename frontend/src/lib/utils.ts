/**
 * Utility functions
 */

/**
 * Format a number as currency (USD)
 */
export function formatCurrency(amount: number | string): string {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(num || 0);
}

/**
 * Format a number of hours
 */
export function formatHours(hours: number | string): string {
    const num = typeof hours === 'string' ? parseFloat(hours) : hours;
    return `${(num || 0).toFixed(1)}h`;
}

/**
 * Format a date string to a readable format
 */
export function formatDate(dateString: string | null): string {
    if (!dateString) return 'N/A';

    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    }).format(date);
}

/**
 * Format a datetime string to a readable format
 */
export function formatDateTime(dateString: string | null): string {
    if (!dateString) return 'N/A';

    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(date);
}

/**
 * Format a time string (HH:MM)
 */
export function formatTime(dateString: string | null): string {
    if (!dateString) return 'N/A';

    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
    }).format(date);
}

/**
 * Get the status badge color class
 */
export function getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
        case 'pending':
            return 'status-pending';
        case 'paid':
        case 'completed':
            return 'status-paid';
        case 'cancelled':
        case 'failed':
            return 'status-cancelled';
        case 'processing':
            return 'status-processing';
        default:
            return 'status-default';
    }
}

/**
 * Get today's date in YYYY-MM-DD format
 */
export function getTodayDate(): string {
    return new Date().toISOString().split('T')[0];
}

/**
 * Get a date N days ago in YYYY-MM-DD format
 */
export function getDateDaysAgo(days: number): string {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date.toISOString().split('T')[0];
}
