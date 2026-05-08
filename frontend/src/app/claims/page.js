'use client';
import { useState } from 'react';
import Shell from '@/components/layout/Shell';
import ClaimRow from '@/components/features/ClaimRow';
import ClaimResult from '@/components/features/ClaimResult';
import { Empty } from '@/components/ui/Misc';
import { useClaimsStore } from '@/hooks/useClaimsStore';
import { shortId } from '@/lib/utils';

const COLUMNS = ['ID', 'File', 'Insured', 'Incident', 'Estimate', 'Completeness', 'Route', 'Pri.'];

export default function ClaimsPage() {
  const { claims, clearClaims } = useClaimsStore();
  const [selected, setSelected] = useState(null);

  const selectedClaim = claims.find((c) => c.claim_id === selected) || null;

  return (
    <Shell title="Claims Registry" subtitle="Session claim history">
      {claims.length === 0 ? (
        <div className="flex items-center justify-center py-32">
          <Empty icon="🗂" message="No claims in this session" sub="Process a PDF from the Upload page to see claims here" />
        </div>
      ) : (
        <div className="flex gap-5 h-[calc(100vh-64px)] overflow-hidden">

          {/* ── Left: Table ── */}
          <div className={`flex flex-col min-w-0 transition-all duration-300 ${selected ? 'w-[55%]' : 'w-full'}`}>

            {/* Table header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--border)] flex-shrink-0">
              <span className="font-mono text-[11px] text-[var(--text-dim)] uppercase tracking-[0.08em]">
                {claims.length} claim{claims.length !== 1 ? 's' : ''} in session
              </span>
              <button
                onClick={() => { clearClaims(); setSelected(null); }}
                className="font-mono text-[11px] text-[var(--text-dim)] hover:text-[var(--red)] transition-colors duration-[var(--t-fast)]"
              >
                Clear all
              </button>
            </div>

            {/* Column headers */}
            <div
              className="grid px-5 py-2 border-b border-[var(--border)] bg-[var(--surface)] flex-shrink-0"
              style={{ gridTemplateColumns: '80px 180px 1fr 140px 110px 140px 150px 60px' }}
            >
              {COLUMNS.map((col) => (
                <span key={col} className="font-mono text-[10px] text-[var(--text-dim)] uppercase tracking-[0.08em]">
                  {col}
                </span>
              ))}
            </div>

            {/* Rows */}
            <div className="flex-1 overflow-y-auto">
              {claims.map((claim) => (
                <ClaimRow
                  key={claim.claim_id}
                  result={claim}
                  active={claim.claim_id === selected}
                  onClick={() => setSelected(claim.claim_id === selected ? null : claim.claim_id)}
                />
              ))}
            </div>
          </div>

          {/* ── Right: Side Panel ── */}
          {selected && (
            <div className="flex flex-col flex-1 min-w-0 border-l border-[var(--border)] overflow-hidden">

              {/* Panel header */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--border)] bg-[var(--surface)] flex-shrink-0">
                <span className="font-mono text-[12px] text-[var(--amber)] tracking-[0.06em]">
                  {shortId(selected)}
                </span>
                <button
                  onClick={() => setSelected(null)}
                  className="w-7 h-7 flex items-center justify-center rounded-[var(--r1)] text-[var(--text-dim)] hover:text-[var(--text)] hover:bg-[var(--border)] transition-all duration-[var(--t-fast)] text-[16px]"
                >
                  ×
                </button>
              </div>

              {/* Scrollable result */}
              <div className="flex-1 overflow-y-auto p-5">
                <ClaimResult result={selectedClaim} />
              </div>
            </div>
          )}
        </div>
      )}
    </Shell>
  );
}