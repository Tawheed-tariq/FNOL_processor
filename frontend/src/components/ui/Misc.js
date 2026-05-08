export function Spinner({ size = 20 }) {
  return (
    <div
      className="rounded-full border-[var(--border)] border-t-[var(--amber)] animate-spin flex-shrink-0"
      style={{
        width: size,
        height: size,
        borderWidth: size > 24 ? 3 : 2,
        borderStyle: 'solid',
      }}
    />
  );
}

export function Stat({ label, value, accent, mono, sub }) {
  return (
    <div className="flex flex-col gap-[3px]">
      <span className="text-[10px] font-mono text-[var(--text-dim)] tracking-[0.08em] uppercase">
        {label}
      </span>
      <span
        className={`
          leading-none font-semibold
          ${accent ? 'text-[var(--amber)]' : 'text-[var(--text)]'}
          ${mono
            ? 'font-mono text-[18px]'
            : 'font-[var(--font-display)] text-[22px]'
          }
        `}
      >
        {value ?? '—'}
      </span>
      {sub && <span className="text-[11px] text-[var(--text-dim)]">{sub}</span>}
    </div>
  );
}

export function Field({ label, value, mono, multiline }) {
  return (
    <>
      <dt className="text-[11px] font-mono text-[var(--text-dim)] tracking-[0.04em] py-2 pr-3 border-b border-[var(--border)] self-start">
        {label}
      </dt>
      <dd
        className={`
          text-[var(--text)] py-2 border-b border-[var(--border)]
          overflow-wrap-break-word break-words
          ${mono    ? 'font-mono text-[12px] tracking-[0.04em]' : 'text-[13px]'}
          ${multiline ? 'whitespace-pre-wrap leading-[1.7] text-[12px]' : ''}
        `}
      >
        {value || <span className="text-[var(--muted)] italic">—</span>}
      </dd>
    </>
  );
}

export function Progress({ value, color }) {
  return (
    <div className="h-[3px] bg-[var(--border)] rounded-full overflow-hidden flex-1">
      <div
        className="h-full rounded-full transition-[width] duration-[600ms] ease-[cubic-bezier(0.4,0,0.2,1)]"
        style={{
          width: `${Math.min(100, Math.max(0, value))}%`,
          background: color || 'var(--amber)',
        }}
      />
    </div>
  );
}

export function Empty({ icon, message, sub }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 px-5 text-center">
      {icon && (
        <span className="text-[32px] opacity-40 grayscale">{icon}</span>
      )}
      <p className="text-[14px] text-[var(--text-dim)]">{message}</p>
      {sub && <p className="text-[12px] text-[var(--muted)]">{sub}</p>}
    </div>
  );
}

export function SectionTitle({ children, mono }) {
  return (
    <h4
      className={`
        uppercase tracking-[0.06em] font-semibold text-[var(--text-dim)] mb-4
        ${mono
          ? 'font-mono text-[11px]'
          : 'font-[var(--font-display)] text-[13px]'
        }
      `}
    >
      {children}
    </h4>
  );
}

export function Tag({ children, color }) {
  return (
    <span
      className="inline-flex items-center py-0.5 px-2 rounded-[3px] font-mono text-[10px] border border-[var(--border)] text-[var(--text-dim)] bg-[var(--surface)] whitespace-nowrap"
      style={color ? { color, borderColor: `${color}40`, background: `${color}10` } : {}}
    >
      {children}
    </span>
  );
}