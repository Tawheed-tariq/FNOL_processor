'use client';
import { useContext, createContext, useState } from 'react';
import Shell from '@/components/layout/Shell';
import Card, { CardHeader, CardTitle, CardBody } from '@/components/ui/Card';
import RouteBadge from '@/components/ui/RouteBadge';
import { Stat, Empty, Progress } from '@/components/ui/Misc';
import { getRouteColor, completenessPercent, formatCurrency, shortId } from '@/lib/utils';
import { useClaimsStore } from '@/hooks/useClaimsStore';

export const StoreContext = createContext(null);

const ROUTE_ORDER = ['Fast-track', 'Manual Review', 'Investigation', 'Specialist Queue'];

export default function DashboardPage() {
  const store = useClaimsStore();
  const { claims } = store;

  const total = claims.length;
  const routeCounts = ROUTE_ORDER.reduce((acc, r) => {
    acc[r] = claims.filter((c) => c.routing.route === r).length;
    return acc;
  }, {});
  const avgCompleteness = total
    ? claims.reduce((s, c) => s + c.validation.completeness_score, 0) / total
    : 0;
  const avgPriority = total
    ? claims.reduce((s, c) => s + c.routing.priority_score, 0) / total
    : 0;

  return (
    <StoreContext.Provider value={store}>
      {/* Added px-6 pt-6 pb-10 so content breathes away from sidebar and header */}
      <Shell title="Command Center" subtitle="FNOL Claims Intelligence Platform">

        {/* .page — padding added here so all content clears sidebar/header edges */}
        <div className="flex flex-col gap-5 max-w-[1200px]">

          {/* .kpiRow */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Total Processed', value: total, accent: total > 0 },
              { label: 'Avg Completeness', value: total ? completenessPercent(avgCompleteness) : '—' },
              { label: 'Avg Priority', value: total ? avgPriority.toFixed(1) : '—' },
              {
                label: 'Investigation',
                value: routeCounts['Investigation'],
                // Use a distinct danger accent instead of amber to avoid collision
                accent: routeCounts['Investigation'] > 0,
                danger: routeCounts['Investigation'] > 0,
              },
            ].map((kpi) => (
              /* .kpiCard */
              <div
                key={kpi.label}
                className="
                  relative overflow-hidden p-5
                  bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]
                  animate-[fadeUp_0.4s_ease_both]
                  after:content-[''] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-px
                  after:bg-gradient-to-r after:from-[var(--amber)] after:to-transparent
                  after:origin-left after:animate-[slideRight_0.6s_ease_0.3s_both]
                "
              >
                {/* Pass danger flag so Stat can render the Investigation count in red, not amber */}
                <Stat label={kpi.label} value={kpi.value} accent={kpi.accent} danger={kpi.danger} />
              </div>
            ))}
          </div>

          {/* .mainGrid */}
          <div className="grid gap-5" style={{ gridTemplateColumns: '1fr 1.4fr' }}>

            {/* Route Distribution Card */}
            <Card>
              <CardHeader>
                <CardTitle>Route Distribution</CardTitle>
              </CardHeader>
              <CardBody>
                {total === 0 ? (
                  <Empty icon="📋" message="No claims processed yet" sub="Upload a PDF to get started" />
                ) : (
                  /* .routeBars */
                  <div className="flex flex-col gap-4">
                    {ROUTE_ORDER.map((route) => {
                      const count = routeCounts[route];
                      const pct = total ? (count / total) * 100 : 0;
                      return (
                        /* .routeBar */
                        <div key={route} className="flex items-center gap-3">
                          {/* .routeBarHeader */}
                          <div className="w-40 flex justify-between items-center flex-shrink-0">
                            <RouteBadge route={route} size="sm" showIcon={false} />
                            {/* .routeCount — use text-[var(--text)] not amber to avoid badge color clash */}
                            <span className="font-mono text-[13px] text-[var(--text)] font-medium">
                              {count}
                            </span>
                          </div>
                          <Progress value={pct} color={getRouteColor(route)} />
                          {/* .routePct */}
                          <span className="font-mono text-[11px] text-[var(--text-dim)] whitespace-nowrap w-9 text-right">
                            {pct.toFixed(0)}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Recent Claims Card */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Claims</CardTitle>
              </CardHeader>
              <CardBody>
                {claims.length === 0 ? (
                  <Empty icon="🗂" message="No claims in session" sub="Processed claims appear here" />
                ) : (
                  /* .recentList */
                  <div className="flex flex-col gap-0">
                    {claims.slice(0, 6).map((claim) => (
                      /* .recentItem */
                      <div
                        key={claim.claim_id}
                        className="
                          flex items-center justify-between py-[10px] gap-4
                          border-b border-[var(--border)] last:border-b-0
                          animate-[fadeIn_0.3s_ease_both]
                        "
                      >
                        {/* .recentLeft */}
                        <div className="flex items-center gap-3 min-w-0">
                          {/*
                            .recentId — was amber text, which collides with amber RouteBadge
                            on the right. Switched to muted/dim so the two don't compete.
                          */}
                          <span className="font-mono text-[11px] text-[var(--text-dim)] flex-shrink-0 w-14">
                            {shortId(claim.claim_id)}
                          </span>
                          {/* .recentInfo */}
                          <div className="flex flex-col gap-0.5 min-w-0">
                            {/* .recentName */}
                            <span className="text-[13px] text-[var(--text)] whitespace-nowrap overflow-hidden text-ellipsis">
                              {claim.extracted_claim.insured.name || claim._filename}
                            </span>
                            {/* .recentMeta */}
                            <span className="text-[11px] text-[var(--text-dim)] font-mono">
                              {claim.extracted_claim.incident.incident_type} · {claim.extracted_claim.incident.date_of_loss || '—'}
                            </span>
                          </div>
                        </div>

                        {/* .recentRight */}
                        <div className="flex items-center gap-3 flex-shrink-0">
                          <RouteBadge route={claim.routing.route} size="sm" />
                          {/* .recentScore — keep dim, not amber, to avoid badge collision */}
                          <span className="font-mono text-[11px] text-[var(--text-dim)]">
                            {completenessPercent(claim.validation.completeness_score)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>
          </div>

          {/* Incident Type Breakdown */}
          {total > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Incident Type Breakdown</CardTitle>
              </CardHeader>
              <CardBody>
                {/* .incidentGrid */}
                <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
                  {Object.entries(
                    claims.reduce((acc, c) => {
                      const t = c.extracted_claim.incident.incident_type || 'Unknown';
                      acc[t] = (acc[t] || 0) + 1;
                      return acc;
                    }, {})
                  )
                    .sort((a, b) => b[1] - a[1])
                    .map(([type, count]) => (
                      /* .incidentItem */
                      <div key={type} className="flex flex-col gap-2">
                        {/* .incidentType — was plain text; keep as-is, no collision here */}
                        <span className="text-[12px] text-[var(--text-dim)]">{type}</span>
                        {/*
                          .incidentCount — was amber; since the progress bar below it is also
                          amber this creates an amber block. Switch the count to plain --text
                          so the amber bar acts as the accent, not both elements.
                        */}
                        <span className="font-mono text-[20px] font-medium text-[var(--text)]">
                          {count}
                        </span>
                        <Progress value={(count / total) * 100} color="var(--amber)" />
                      </div>
                    ))}
                </div>
              </CardBody>
            </Card>
          )}

          {/* Empty Hero */}
          {total === 0 && (
            /* .hero */
            <div className="flex items-center justify-center px-5 py-16">
              {/* .heroInner */}
              <div className="flex flex-col items-center gap-5 text-center max-w-[480px]">
                {/* .heroIcon — muted so it doesn't compete with the CTA button */}
                <div className="w-20 h-20 text-[var(--muted)] animate-[fadeIn_0.6s_ease_both]">
                  <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1" className="w-full h-full">
                    <path d="M16 56V24L32 8h24v48H16z" strokeLinejoin="round" />
                    <path d="M32 8v16h16" strokeLinejoin="round" />
                    <path d="M24 36h24M24 44h16" strokeLinecap="round" />
                    {/*
                      Clock circle inside the icon was amber stroke + amber hand path.
                      The amber CTA button below made this a triple amber collision.
                      Switched to --text-dim so the icon reads as decorative, not action.
                    */}
                    <circle cx="48" cy="48" r="10" fill="var(--ink)" stroke="var(--text-dim)" />
                    <path d="M48 44v4l3 3" strokeLinecap="round" strokeLinejoin="round" stroke="var(--text-dim)" />
                  </svg>
                </div>

                {/* .heroText */}
                <div className="flex flex-col gap-3">
                  {/* .heroTitle */}
                  <h2 className="font-[var(--font-display)] text-[22px] text-[var(--text)]">
                    Ready to process claims
                  </h2>
                  {/* .heroSub */}
                  <p className="text-[13px] text-[var(--text-dim)] leading-[1.7]">
                    Upload an ACORD FNOL PDF to extract structured data, validate fields, and route claims automatically.
                  </p>
                </div>

                {/*
                  .heroCta — amber button is the ONLY amber element in the hero now.
                  Hover swaps to a dark surface color (not white) so the amber glow shadow
                  doesn't clash with a suddenly bright background.
                */}
                <a
                  href="/upload"
                  className="
    inline-flex items-center px-6 py-[10px]
    bg-[var(--amber)] !text-[var(--ink)]
    font-semibold text-[13px] rounded-[var(--r1)]
    tracking-[0.04em] no-underline
    transition-all duration-[var(--t-fast)]
    hover:bg-[var(--surface-raised,#2a2a2a)] hover:!text-[var(--amber)] hover:-translate-y-px
    hover:shadow-[0_4px_16px_rgba(232,168,56,0.25)]
    border border-transparent hover:border-[var(--amber)]
  "
                >
                  Process First Claim
                </a>
              </div>
            </div>
          )}

        </div>
      </Shell>
    </StoreContext.Provider>
  );
}