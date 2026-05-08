'use client';
import { useState, useRef } from 'react';
import Shell from '@/components/layout/Shell';
import Card, { CardHeader, CardTitle, CardBody } from '@/components/ui/Card';
import UploadZone from '@/components/ui/UploadZone';
import ClaimResult from '@/components/features/ClaimResult';
import { Spinner } from '@/components/ui/Misc';
import { useClaimsStore } from '@/hooks/useClaimsStore';
import { formatBytes } from '@/lib/utils';

const MODE_SINGLE = 'single';
const MODE_BATCH  = 'batch';

export default function UploadPage() {
  const { submitSingle, submitBatch, processing, uploadProgress, error, clearError } = useClaimsStore();
  const [mode, setMode]         = useState(MODE_SINGLE);
  const [queued, setQueued]     = useState([]);   // files staged for upload
  const [result, setResult]     = useState(null); // last single result
  const [batchResult, setBatchResult] = useState(null);
  const resultRef = useRef(null);

  const scrollToResult = () =>
    setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);

  const handleFiles = (files) => {
    clearError();
    setResult(null);
    setBatchResult(null);
    setQueued(mode === MODE_SINGLE ? [files[0]] : files.slice(0, 10));
  };

  const handleSubmit = async () => {
    if (!queued.length) return;
    if (mode === MODE_SINGLE) {
      const res = await submitSingle(queued[0]);
      if (res) { setResult(res); scrollToResult(); }
    } else {
      const res = await submitBatch(queued);
      if (res) { setBatchResult(res); scrollToResult(); }
    }
    setQueued([]);
  };

  return (
    <Shell title="Process Claim" subtitle="FNOL Document Ingestion">
      <div className="flex flex-col gap-5 max-w-[900px]">

        {/* Mode Toggle */}
        <div className="flex gap-0 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)] p-1 w-fit">
          {[MODE_SINGLE, MODE_BATCH].map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setQueued([]); setResult(null); setBatchResult(null); }}
              className={`
                px-5 py-2 rounded-[var(--r1)] text-[13px] font-medium transition-all duration-[var(--t-fast)]
                ${mode === m
                  ? 'bg-[var(--amber)] text-[var(--ink)]'
                  : 'text-[var(--text-dim)] hover:text-[var(--text)]'
                }
              `}
            >
              {m === MODE_SINGLE ? 'Single Claim' : 'Batch Upload'}
            </button>
          ))}
        </div>

        {/* Upload Card */}
        <Card>
          <CardHeader>
            <CardTitle>{mode === MODE_SINGLE ? 'Upload FNOL PDF' : 'Batch Upload (max 10)'}</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="flex flex-col gap-4">
              <UploadZone
                onFiles={handleFiles}
                multiple={mode === MODE_BATCH}
                disabled={processing}
              />

              {/* Queued files */}
              {queued.length > 0 && (
                <div className="flex flex-col gap-2">
                  {queued.map((f, i) => (
                    <div key={i} className="flex items-center justify-between px-4 py-2 bg-[var(--ink)] border border-[var(--border)] rounded-[var(--r1)]">
                      <div className="flex items-center gap-3">
                        <span className="text-[var(--amber)] text-[12px]">📄</span>
                        <span className="text-[13px] text-[var(--text)] truncate max-w-[400px]">{f.name}</span>
                      </div>
                      <span className="font-mono text-[11px] text-[var(--text-dim)]">{formatBytes(f.size)}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="flex items-center gap-3 px-4 py-3 bg-[rgba(232,83,58,0.08)] border border-[rgba(232,83,58,0.2)] rounded-[var(--r1)]">
                  <span className="text-[var(--red)]">⚠</span>
                  <span className="text-[13px] text-[var(--red)]">{error}</span>
                </div>
              )}

              {/* Upload progress */}
              {processing && uploadProgress > 0 && uploadProgress < 100 && (
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between">
                    <span className="text-[11px] font-mono text-[var(--text-dim)]">Uploading…</span>
                    <span className="text-[11px] font-mono text-[var(--amber)]">{uploadProgress}%</span>
                  </div>
                  <div className="h-[3px] bg-[var(--border)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[var(--amber)] rounded-full transition-[width] duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Processing indicator */}
              {processing && uploadProgress === 0 && (
                <div className="flex items-center gap-3 text-[13px] text-[var(--text-dim)]">
                  <Spinner size={16} />
                  <span>Extracting with LLM… this may take 10–30s</span>
                </div>
              )}

              {/* Submit */}
              <button
                onClick={handleSubmit}
                disabled={!queued.length || processing}
                className="
                  self-start flex items-center gap-2 px-6 py-[10px]
                  bg-[var(--amber)] text-[var(--ink)] font-semibold text-[13px]
                  rounded-[var(--r1)] tracking-[0.04em]
                  transition-all duration-[var(--t-fast)]
                  hover:bg-white hover:-translate-y-px
                  disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none
                "
              >
                {processing ? <><Spinner size={14} /> Processing…</> : `Process ${mode === MODE_BATCH ? `${queued.length} File${queued.length !== 1 ? 's' : ''}` : 'Claim'}`}
              </button>
            </div>
          </CardBody>
        </Card>

        {/* Single result */}
        {result && (
          <div ref={resultRef}>
            <ClaimResult result={result} />
          </div>
        )}

        {/* Batch summary */}
        {batchResult && (
          <div ref={resultRef} className="flex flex-col gap-4">
            <div className="flex items-center gap-4 px-5 py-4 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--r2)]">
              <span className="font-mono text-[13px] text-[var(--text-dim)]">
                Batch complete —
              </span>
              <span className="font-mono text-[13px] text-[var(--green)]">✓ {batchResult.succeeded} succeeded</span>
              {batchResult.failed > 0 && (
                <span className="font-mono text-[13px] text-[var(--red)]">✗ {batchResult.failed} failed</span>
              )}
            </div>
            {batchResult.items
              .filter((item) => item.status === 'success' && item.response)
              .map((item, i) => (
                <ClaimResult key={i} result={{ ...item.response, _filename: item.filename }} />
              ))}
          </div>
        )}
      </div>
    </Shell>
  );
}