'use client';
import { useState } from 'react';
import Card, { CardHeader, CardTitle, CardBody } from '@/components/ui/Card';
import RouteBadge from '@/components/ui/RouteBadge';
import { Field, Stat, Progress, SectionTitle, Tag } from '@/components/ui/Misc';
import { getSeverityColor, formatCurrency, formatDuration, completenessPercent, shortId, getRouteColor } from '@/lib/utils';

const TABS = ['Overview', 'Parties', 'Vehicle', 'Validation', 'Raw'];

export default function ClaimResult({ result }) {
  const [tab, setTab] = useState('Overview');
  if (!result) return null;

  const { extracted_claim: c, validation: v, routing: r, metadata: m } = result;

  const completenessColor =
    v.completeness_score > 0.7 ? 'var(--green)'
    : v.completeness_score > 0.4 ? 'var(--amber)'
    : 'var(--red)';

  return (
    <div className="flex flex-col gap-4 animate-[fadeUp_0.35s_ease_both]">

      {/* Top Bar */}
      <div className="flex items-center justify-between gap-5 px-5 py-4 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]">
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-[0.08em]">Claim ID</span>
          <span className="font-mono text-[16px] font-medium text-[var(--amber)] tracking-[0.06em]">{shortId(result.claim_id)}</span>
          <span className="font-mono text-[11px] text-[var(--muted)] tracking-[0.04em]">{result.claim_id}</span>
        </div>
        <div className="flex items-center gap-3">
          <RouteBadge route={r.route} size="lg" />
          <span
            className="font-mono text-[12px] font-medium"
            style={{ color: result.status === 'success' ? 'var(--green)' : 'var(--amber)' }}
          >
            {result.status === 'success' ? '✓ Valid' : '⚠ Partial'}
          </span>
        </div>
      </div>

      {/* Meta Row */}
      <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 2fr 1fr 1fr' }}>
        {/* Priority */}
        <div className="flex flex-col gap-2 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]">
          <span className="text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-[0.08em]">Priority</span>
          <div className="flex items-center gap-[3px]">
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                className="w-[10px] h-[10px] rounded-[2px] transition-colors duration-[var(--t-base)]"
                style={{ background: i < r.priority_score ? getRouteColor(r.route) : 'var(--border)' }}
              />
            ))}
            <span className="font-mono text-[11px] text-[var(--text-dim)] ml-2">{r.priority_score}/10</span>
          </div>
        </div>

        {/* Completeness */}
        <div className="flex flex-col gap-2 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]">
          <span className="text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-[0.08em]">Data Completeness</span>
          <div className="flex items-center gap-3">
            <Progress value={v.completeness_score * 100} color={completenessColor} />
            <span className="font-mono text-[13px] text-[var(--text)] whitespace-nowrap">
              {completenessPercent(v.completeness_score)}
            </span>
          </div>
        </div>

        {/* Processing time */}
        <div className="flex flex-col gap-2 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]">
          <span className="text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-[0.08em]">Processed in</span>
          <span className="font-mono text-[13px] text-[var(--text)]">{formatDuration(m.processing_time_ms)}</span>
        </div>

        {/* Pages / Model */}
        <div className="flex flex-col gap-2 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]">
          <span className="text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-[0.08em]">Pages / Model</span>
          <span className="font-mono text-[13px] text-[var(--text)]">{m.pages_extracted} pp · {m.llm_model}</span>
        </div>
      </div>

      {/* Reasoning */}
      <div className="flex gap-3 px-5 py-4 bg-[var(--surface)] border border-[var(--border)] border-l-2 border-l-[var(--amber)] rounded-[var(--r2)]">
        <span className="text-[var(--amber)] text-[16px] flex-shrink-0 mt-px">◈</span>
        <p className="text-[13px] text-[var(--text)] leading-[1.7]">{r.reasoning}</p>
      </div>

      {/* Flags */}
      {r.flags?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {r.flags.map((flag, i) => (
            <Tag key={i} color="var(--amber)">{flag}</Tag>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-[var(--border)]">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`
              flex items-center gap-2 px-5 py-3 text-[13px] cursor-pointer
              border-b-2 -mb-px transition-all duration-[var(--t-fast)]
              bg-transparent border-x-0 border-t-0
              ${tab === t
                ? 'text-[var(--amber)] border-b-[var(--amber)]'
                : 'text-[var(--text-dim)] border-b-transparent hover:text-[var(--text)]'
              }
            `}
          >
            {t}
            {t === 'Validation' && v.issues.length > 0 && (
              <span className="bg-[var(--red)] text-white text-[9px] font-mono font-semibold px-[5px] py-px rounded-full">
                {v.issues.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Panel */}
      <div className="animate-[fadeIn_0.2s_ease_both]">
        {tab === 'Overview'   && <OverviewPanel c={c} />}
        {tab === 'Parties'    && <PartiesPanel c={c} />}
        {tab === 'Vehicle'    && <VehiclePanel c={c} />}
        {tab === 'Validation' && <ValidationPanel v={v} />}
        {tab === 'Raw'        && <RawPanel result={result} />}
      </div>
    </div>
  );
}

/* ── Shared field grid wrapper ── */
function FieldGrid({ children }) {
  return (
    <dl className="grid gap-0" style={{ gridTemplateColumns: '140px 1fr' }}>
      {children}
    </dl>
  );
}

/* ── Description block ── */
function DescBlock({ label, text }) {
  return (
    <div className="mt-4 p-4 bg-[var(--ink)] border border-[var(--border)] rounded-[var(--r2)]">
      <p className="text-[10px] font-mono text-[var(--text-dim)] uppercase tracking-[0.08em] mb-2">{label}</p>
      <p className="text-[13px] text-[var(--text)] leading-[1.7]">{text}</p>
    </div>
  );
}

function OverviewPanel({ c }) {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <Card>
        <CardHeader><CardTitle>Policy</CardTitle></CardHeader>
        <CardBody>
          <FieldGrid>
            <Field label="Policy No."      value={c.policy.policy_number}   mono />
            <Field label="Carrier"         value={c.policy.carrier} />
            <Field label="NAIC Code"       value={c.policy.naic_code}       mono />
            <Field label="Line of Business"value={c.policy.line_of_business} />
            <Field label="Agency"          value={c.policy.agency_name} />
            <Field label="Agency Code"     value={c.policy.agency_code}     mono />
          </FieldGrid>
        </CardBody>
      </Card>
      <Card>
        <CardHeader><CardTitle>Incident</CardTitle></CardHeader>
        <CardBody>
          <FieldGrid>
            <Field label="Date of Loss"     value={c.incident.date_of_loss}           mono />
            <Field label="Time"             value={c.incident.time_of_loss}           mono />
            <Field label="Type"             value={c.incident.incident_type} />
            <Field label="Street"           value={c.incident.location_street} />
            <Field label="City / State / ZIP" value={c.incident.location_city_state_zip} />
            <Field label="Police Contacted" value={c.incident.police_contacted === true ? 'Yes' : c.incident.police_contacted === false ? 'No' : null} />
            <Field label="Report No."       value={c.incident.report_number}          mono />
          </FieldGrid>
          {c.incident.description && <DescBlock label="Description" text={c.incident.description} />}
        </CardBody>
      </Card>
    </div>
  );
}

function PartiesPanel({ c }) {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <Card>
        <CardHeader><CardTitle>Insured</CardTitle></CardHeader>
        <CardBody>
          <FieldGrid>
            <Field label="Name"    value={c.insured.name} />
            <Field label="DOB"     value={c.insured.date_of_birth}   mono />
            <Field label="Phone"   value={c.insured.primary_phone}   mono />
            <Field label="Email"   value={c.insured.email} />
            <Field label="Address" value={c.insured.mailing_address} />
          </FieldGrid>
        </CardBody>
      </Card>
      <Card>
        <CardHeader><CardTitle>Driver</CardTitle></CardHeader>
        <CardBody>
          <FieldGrid>
            <Field label="Name"           value={c.driver.name} />
            <Field label="Relation"       value={c.driver.relation_to_insured} />
            <Field label="License"        value={c.driver.license_number}  mono />
            <Field label="License State"  value={c.driver.license_state}   mono />
            <Field label="DOB"            value={c.driver.date_of_birth}   mono />
            <Field label="Purpose"        value={c.driver.purpose_of_use} />
            <Field label="With Permission"value={c.driver.used_with_permission === true ? 'Yes' : c.driver.used_with_permission === false ? 'No ⚠' : null} />
          </FieldGrid>
        </CardBody>
      </Card>
      {c.injured_parties?.length > 0 && (
        <div className="col-span-2">
          <Card>
            <CardHeader><CardTitle>Injured Parties ({c.injured_parties.length})</CardTitle></CardHeader>
            <CardBody>
              <div className="flex flex-col gap-2">
                {c.injured_parties.map((p, i) => (
                  <div key={i} className="flex items-center gap-3 px-4 py-3 bg-[var(--ink)] border border-[var(--border)] rounded-[var(--r2)]">
                    <span className="font-mono text-[11px] text-[var(--amber)]">{String(i + 1).padStart(2, '0')}</span>
                    <div className="flex flex-col gap-0.5 text-[13px]">
                      <span>{p.name || '—'}</span>
                      <span className="text-[11px] text-[var(--text-dim)]">{p.extent_of_injury || ''}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}

function VehiclePanel({ c }) {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 1fr' }}>
      <Card>
        <CardHeader><CardTitle>Insured Vehicle</CardTitle></CardHeader>
        <CardBody>
          <FieldGrid>
            <Field label="Year / Make / Model" value={[c.vehicle.year, c.vehicle.make, c.vehicle.model].filter(Boolean).join(' ')} />
            <Field label="Body Type"         value={c.vehicle.body_type} />
            <Field label="VIN"               value={c.vehicle.vin}            mono />
            <Field label="Plate"             value={`${c.vehicle.plate_number || '—'} · ${c.vehicle.plate_state || ''}`} mono />
            <Field label="Damage Estimate"   value={formatCurrency(c.vehicle.estimate_amount)} />
            <Field label="Where to Inspect"  value={c.vehicle.where_can_be_seen} />
            <Field label="When"              value={c.vehicle.when_can_be_seen} />
          </FieldGrid>
          {c.vehicle.damage_description && <DescBlock label="Damage Description" text={c.vehicle.damage_description} />}
        </CardBody>
      </Card>
      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader><CardTitle>Child Seat</CardTitle></CardHeader>
          <CardBody>
            <FieldGrid>
              <Field label="Installed"         value={c.child_seat.installed === true ? 'Yes' : c.child_seat.installed === false ? 'No' : null} />
              <Field label="In Use"            value={c.child_seat.in_use_by_child === true ? 'Yes' : c.child_seat.in_use_by_child === false ? 'No' : null} />
              <Field label="Sustained Damage"  value={c.child_seat.sustained_loss === true ? 'Yes ⚠' : c.child_seat.sustained_loss === false ? 'No' : null} />
            </FieldGrid>
          </CardBody>
        </Card>
        {c.third_party_vehicles?.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Third Party Vehicles ({c.third_party_vehicles.length})</CardTitle></CardHeader>
            <CardBody>
              <div className="flex flex-col">
                {c.third_party_vehicles.map((v, i) => (
                  <div key={i} className="flex items-center gap-3 py-3 border-b border-[var(--border)] last:border-b-0 text-[13px]">
                    <span className="font-mono text-[11px] text-[var(--blue)] w-6">V{i + 1}</span>
                    <span>{[v.year, v.make, v.model].filter(Boolean).join(' ') || '—'}</span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}

function ValidationPanel({ v }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-4 gap-4 p-5 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]">
        <Stat label="Status"           value={v.is_valid ? 'Valid' : 'Invalid'}          accent={!v.is_valid} />
        <Stat label="Missing Required" value={v.missing_required_fields.length}           accent={v.missing_required_fields.length > 0} />
        <Stat label="Issues"           value={v.issues.length} />
        <Stat label="Completeness"     value={completenessPercent(v.completeness_score)} />
      </div>

      {v.missing_required_fields.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Missing Required Fields</CardTitle></CardHeader>
          <CardBody>
            <div className="flex flex-col gap-2">
              {v.missing_required_fields.map((f, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="w-[5px] h-[5px] rounded-full bg-[var(--red)] flex-shrink-0" />
                  <code className="font-mono text-[12px] text-[var(--red)]">{f}</code>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {v.issues.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Validation Issues</CardTitle></CardHeader>
          <CardBody>
            <div className="flex flex-col gap-3">
              {v.issues.map((issue, i) => (
                <div key={i} className="flex gap-4 p-4 bg-[var(--ink)] border border-[var(--border)] rounded-[var(--r2)]">
                  <span
                    className="font-mono text-[10px] font-medium tracking-[0.06em] whitespace-nowrap pt-0.5 min-w-[56px]"
                    style={{ color: getSeverityColor(issue.severity) }}
                  >
                    {issue.severity.toUpperCase()}
                  </span>
                  <div className="flex flex-col gap-[3px]">
                    <code className="font-mono text-[11px] text-[var(--text-dim)]">{issue.field}</code>
                    <p className="text-[12px] text-[var(--text)] leading-[1.5]">{issue.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function RawPanel({ result }) {
  return (
    <Card>
      <CardHeader><CardTitle mono>Raw JSON Output</CardTitle></CardHeader>
      <CardBody>
        <pre className="font-mono text-[11px] text-[var(--text-dim)] bg-[var(--ink)] p-5 rounded-[var(--r2)] overflow-auto max-h-[500px] leading-[1.6] border border-[var(--border)]">
          {JSON.stringify(result, null, 2)}
        </pre>
      </CardBody>
    </Card>
  );
}