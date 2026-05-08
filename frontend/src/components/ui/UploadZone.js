'use client';
import { useRef, useState } from 'react';
import { formatBytes } from '@/lib/utils';

export default function UploadZone({ onFiles, multiple = false, disabled = false }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleFiles = (files) => {
    const pdfs = Array.from(files).filter((f) => f.type === 'application/pdf');
    if (pdfs.length) onFiles(multiple ? pdfs : [pdfs[0]]);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (!disabled) handleFiles(e.dataTransfer.files);
  };

  return (
    <div
      className={`
        relative flex flex-col items-center justify-center gap-4
        border-2 border-dashed rounded-[var(--r2)] p-12 text-center
        transition-all duration-[var(--t-fast)] cursor-pointer
        ${dragging
          ? 'border-[var(--amber)] bg-[var(--amber-glow)]'
          : 'border-[var(--border)] hover:border-[var(--muted)] hover:bg-[rgba(255,255,255,0.01)]'
        }
        ${disabled ? 'opacity-50 pointer-events-none' : ''}
      `}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        multiple={multiple}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {/* Icon */}
      <div className={`transition-colors duration-[var(--t-fast)] ${dragging ? 'text-[var(--amber)]' : 'text-[var(--muted)]'}`}>
        <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-12 h-12">
          <path d="M12 40V28L24 8l12 20v12H12z" strokeLinejoin="round" />
          <path d="M24 8v16M18 34h12" strokeLinecap="round" />
          <circle cx="38" cy="36" r="8" fill="var(--ink)" stroke="var(--amber)" strokeWidth="1.5" />
          <path d="M38 32v4l3 3" stroke="var(--amber)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" />
        </svg>
      </div>

      <div className="flex flex-col gap-1">
        <p className="text-[15px] text-[var(--text)] font-medium">
          {dragging ? 'Drop to process' : `Drop PDF${multiple ? 's' : ''} here`}
        </p>
        <p className="text-[12px] text-[var(--text-dim)]">
          or click to browse · {multiple ? 'up to 10 files' : 'single file'} · max 20 MB each
        </p>
      </div>
    </div>
  );
}