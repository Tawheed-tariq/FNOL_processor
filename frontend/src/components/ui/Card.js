import { } from 'react';

export default function Card({ children, className = '', accent, style }) {
  return (
    <div
      className={`
        bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]
        overflow-hidden transition-colors duration-[var(--t-base)]
        hover:border-[var(--muted)]
        ${accent ? 'border-l-2 border-l-[var(--amber)]' : ''}
        ${className}
      `}
      style={style}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, action }) {
  return (
    <div className="flex items-start justify-between pt-5 px-5 gap-4">
      <div className="flex flex-col gap-1">{children}</div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

export function CardTitle({ children, mono }) {
  return (
    <h3
      className={
        mono
          ? 'font-mono text-[13px] font-medium tracking-[0.04em] text-[var(--text)]'
          : 'font-[var(--font-display)] text-[15px] font-semibold text-[var(--text)]'
      }
    >
      {children}
    </h3>
  );
}

export function CardSubtitle({ children }) {
  return <p className="text-[12px] text-[var(--text-dim)]">{children}</p>;
}

export function CardBody({ children }) {
  return <div className="p-5">{children}</div>;
}