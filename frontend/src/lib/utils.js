/** Format a file size in bytes to human-readable string */
export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Format milliseconds to a readable duration */
export function formatDuration(ms) {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/** Format a currency amount */
export function formatCurrency(amount) {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount);
}

/** Return route colour token */
export function getRouteColor(route) {
  const map = {
    'Fast-track':      'var(--green)',
    'Manual Review':   'var(--amber)',
    'Investigation':   'var(--red)',
    'Specialist Queue':'var(--blue)',
  };
  return map[route] || 'var(--muted)';
}

/** Return route background colour token */
export function getRouteBg(route) {
  const map = {
    'Fast-track':      'var(--green-dim)',
    'Manual Review':   'var(--amber-dim)',
    'Investigation':   'var(--red-dim)',
    'Specialist Queue':'var(--blue-dim)',
  };
  return map[route] || 'var(--muted)';
}

/** Return severity colour */
export function getSeverityColor(severity) {
  return { error: 'var(--red)', warning: 'var(--amber)', info: 'var(--blue)' }[severity] || 'var(--muted)';
}

/** Truncate a string to maxLen characters */
export function truncate(str, maxLen = 80) {
  if (!str) return '—';
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
}

/** Format a date string nicely */
export function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
  } catch {
    return dateStr;
  }
}

/** Generate a short ID for display */
export function shortId(uuid) {
  if (!uuid) return '—';
  return uuid.split('-')[0].toUpperCase();
}

/** Completeness score to percentage string */
export function completenessPercent(score) {
  return `${Math.round((score || 0) * 100)}%`;
}