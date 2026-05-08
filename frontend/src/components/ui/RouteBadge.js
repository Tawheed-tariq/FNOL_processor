import { getRouteColor, getRouteBg } from '@/lib/utils';

const ROUTE_ICONS = {
  'Fast-track':      '⚡',
  'Manual Review':   '👁',
  'Investigation':   '🔍',
  'Specialist Queue':'⚕',
};

const sizeClasses = {
  sm: 'text-[10px] py-0.5 px-[7px]',
  md: 'text-[11px] py-[3px] px-[9px]',
  lg: 'text-[13px] py-[5px] px-3',
};

export default function RouteBadge({ route, size = 'md', showIcon = true }) {
  if (!route) return (
    <span className="text-[var(--muted)] font-mono">—</span>
  );

  const color = getRouteColor(route);
  const bg    = getRouteBg(route);

  return (
    <span
      className={`
        inline-flex items-center gap-[5px]
        border border-transparent rounded-[3px]
        font-mono font-medium tracking-[0.03em] whitespace-nowrap
        ${sizeClasses[size]}
      `}
      style={{ color, background: `${bg}40`, borderColor: `${color}40` }}
    >
      {showIcon && (
        <span className="text-[0.9em]">{ROUTE_ICONS[route] || '•'}</span>
      )}
      {route}
    </span>
  );
}