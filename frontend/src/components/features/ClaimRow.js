import RouteBadge from '@/components/ui/RouteBadge';
import { Progress } from '@/components/ui/Misc';
import { shortId, completenessPercent, formatCurrency, getRouteColor } from '@/lib/utils';

export default function ClaimRow({ result, onClick, active }) {
  const { extracted_claim: c, validation: v, routing: r, metadata: m } = result;

  const completenessColor =
    v.completeness_score > 0.7 ? 'var(--green)'
    : v.completeness_score > 0.4 ? 'var(--amber)'
    : 'var(--red)';

  return (
    <div
      className={`
        grid items-center gap-4 py-3 px-5
        border-b border-[var(--border)] cursor-pointer
        transition-colors duration-[var(--t-fast)]
        hover:bg-[rgba(255,255,255,0.02)]
        ${active
          ? 'bg-[var(--amber-glow)] border-l-2 border-l-[var(--amber)]'
          : 'border-l-2 border-l-transparent'
        }
      `}
      style={{ gridTemplateColumns: '80px 180px 1fr 140px 110px 140px 150px 60px' }}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
    >
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="font-mono text-[12px] text-[var(--amber)] font-medium tracking-[0.06em]">
          {shortId(result.claim_id)}
        </span>
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-[12px] text-[var(--text)] truncate">{result._filename || m.filename}</span>
        <span className="font-mono text-[10px] text-[var(--text-dim)]">{m.pages_extracted} pp</span>
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-[13px] text-[var(--text)] truncate">{c.insured.name || '—'}</span>
        <span className="font-mono text-[10px] text-[var(--text-dim)] truncate">{c.policy.policy_number || ''}</span>
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="text-[13px] text-[var(--text)] truncate">{c.incident.incident_type || '—'}</span>
        <span className="font-mono text-[10px] text-[var(--text-dim)]">{c.incident.date_of_loss || ''}</span>
      </div>
      <div className="flex flex-col gap-0.5 min-w-0">
        <span className="font-mono text-[12px] text-[var(--text)]">{formatCurrency(c.vehicle.estimate_amount)}</span>
      </div>
      <div className="flex items-center gap-2">
        <Progress value={v.completeness_score * 100} color={completenessColor} />
        <span className="font-mono text-[11px] text-[var(--text-dim)] whitespace-nowrap">
          {completenessPercent(v.completeness_score)}
        </span>
      </div>
      <div className="flex items-center">
        <RouteBadge route={r.route} size="sm" />
      </div>
      <div className="flex items-center justify-center">
        <span className="font-mono text-[16px] font-semibold" style={{ color: getRouteColor(r.route) }}>
          {r.priority_score}
        </span>
      </div>
    </div>
  );
}