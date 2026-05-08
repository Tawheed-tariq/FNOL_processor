'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Upload, ClipboardList } from 'lucide-react';

const NAV = [
  { href: '/',        label: 'Dashboard',       icon: LayoutDashboard },
  { href: '/upload',  label: 'Process Claim',   icon: Upload },
  { href: '/claims',  label: 'Claims Registry', icon: ClipboardList },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[220px] min-h-screen bg-[var(--surface)] border-r border-[var(--border)] flex flex-col sticky top-0 p-5 gap-4 flex-shrink-0">

      {/* Logo */}
      <div className="flex items-center gap-3 py-2 pb-3">
        <div className="w-9 h-9 bg-[var(--amber)] rounded-[var(--r1)] flex items-center justify-center flex-shrink-0">
          <span className="font-[var(--font-display)] text-[18px] font-bold text-[var(--ink)] leading-none">
            F
          </span>
        </div>
        <div className="flex flex-col gap-px">
          <span className="font-mono text-[15px] font-medium text-white tracking-[0.08em]">
            FNOL
          </span>
          <span className="text-[10px] text-[var(--text-dim)] tracking-[0.06em] uppercase">
            Claims Intelligence
          </span>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-[var(--border)] -mx-5" />

      {/* Nav */}
      <nav className="flex flex-col gap-0.5 flex-1">
        <p className="text-[10px] font-mono text-[var(--text-dim)] tracking-[0.1em] uppercase py-4 pb-2">
          Navigation
        </p>
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`
                relative flex items-center gap-3 py-[10px] px-3 rounded-[var(--r2)]
                text-[13px] no-underline transition-all duration-[var(--t-fast)]
                ${active
                  ? 'bg-[var(--amber-glow)] text-[var(--amber)] font-medium'
                  : 'text-[var(--text-dim)] font-normal hover:bg-[var(--border)] hover:text-[var(--text)]'
                }
              `}
            >
              <Icon size={16} strokeWidth={1.6} className="flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {active && (
                <span className="absolute right-0 top-1/4 bottom-1/4 w-0.5 bg-[var(--amber)] rounded-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t border-[var(--border)] pt-4 flex flex-col gap-2">
        <div className="flex items-center gap-2 font-mono text-[11px] text-[var(--text-dim)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--green)] shadow-[0_0_6px_var(--green)] animate-[dotPulse_2s_infinite]" />
          <span>v1.0.0</span>
        </div>
        <p className="text-[10px] text-[var(--muted)] tracking-[0.04em]">
          ACORD FNOL Processor
        </p>
      </div>
    </aside>
  );
}