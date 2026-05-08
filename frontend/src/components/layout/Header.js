'use client';
import { useState, useEffect } from 'react';
import { checkReadiness } from '@/lib/api';

export default function Header({ title, subtitle }) {
  const [systemStatus, setSystemStatus] = useState(null);
  const [time, setTime] = useState('');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const r = await checkReadiness();
        setSystemStatus(r);
      } catch {
        setSystemStatus({ status: 'degraded' });
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false }));
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  const isReady = systemStatus?.status === 'ready';
  const isLoading = systemStatus === null;

  const statusVariant = isLoading ? 'loading' : isReady ? 'ready' : 'degraded';

  const badgeClasses = {
    ready:    'text-[var(--green)]  bg-[rgba(46,204,138,0.08)]  border-[rgba(46,204,138,0.2)]',
    degraded: 'text-[var(--red)]   bg-[rgba(232,83,58,0.08)]   border-[rgba(232,83,58,0.2)]',
    loading:  'text-[var(--amber)] bg-[var(--amber-glow)]       border-[rgba(232,168,56,0.2)]',
  };

  const dotClasses = {
    ready:    'bg-[var(--green)]  shadow-[0_0_5px_var(--green)]',
    degraded: 'bg-[var(--red)]',
    loading:  'bg-[var(--amber)] animate-[blink_1s_infinite]',
  };

  return (
    <header className="h-16 border-b border-[var(--border)] flex items-center justify-between px-6 bg-[var(--ink)] sticky top-0 z-50 gap-5">

      {/* Left */}
      <div className="flex flex-col justify-center">
        {title && (
          <h1 className="font-[var(--font-display)] text-[18px] font-semibold text-white leading-[1.1]">
            {title}
          </h1>
        )}
        {subtitle && (
          <p className="text-[11px] text-[var(--text-dim)] font-mono tracking-[0.04em] mt-px">
            {subtitle}
          </p>
        )}
      </div>

      {/* Right */}
      <div className="flex items-center gap-4 flex-shrink-0">

        {/* Clock */}
        <div className="flex flex-col items-end gap-px">
          <span className="font-mono text-[13px] font-medium text-[var(--text)] tracking-[0.06em]">
            {time}
          </span>
          <span className="font-mono text-[10px] text-[var(--text-dim)] tracking-[0.04em]">
            {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
          </span>
        </div>

        {/* Separator */}
        <div className="w-px h-8 bg-[var(--border)]" />

        {/* System Status */}
        <StatusGroup
          label="System"
          variant={statusVariant}
          badgeClasses={badgeClasses}
          dotClasses={dotClasses}
        >
          {isLoading ? 'Checking' : isReady ? 'Operational' : 'Degraded'}
        </StatusGroup>

        {/* Ollama Status */}
        {systemStatus && (
          <StatusGroup
            label="Ollama LLM"
            variant={systemStatus.ollama?.ok ? 'ready' : 'degraded'}
            badgeClasses={badgeClasses}
            dotClasses={dotClasses}
          >
            {systemStatus.ollama?.ok
              ? `Online · ${systemStatus.configured_model || ''}`
              : 'Offline'}
          </StatusGroup>
        )}
      </div>
    </header>
  );
}

function StatusGroup({ label, variant, badgeClasses, dotClasses, children }) {
  return (
    <div className="flex flex-col items-start gap-[3px]">
      <span className="text-[10px] text-[var(--text-dim)] font-mono tracking-[0.06em] uppercase">
        {label}
      </span>
      <div className={`flex items-center gap-[5px] font-mono text-[11px] py-0.5 px-2 rounded-full border ${badgeClasses[variant]}`}>
        <span className={`w-[5px] h-[5px] rounded-full flex-shrink-0 ${dotClasses[variant]}`} />
        <span>{children}</span>
      </div>
    </div>
  );
}