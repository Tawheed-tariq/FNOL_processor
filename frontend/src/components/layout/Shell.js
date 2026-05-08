'use client';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Shell({ title, subtitle, children }) {
  return (
    <div className="flex min-h-screen bg-[var(--ink)]">

      <Sidebar />

      {/* Right column: header + scrollable content */}
      <div className="flex flex-col flex-1 min-w-0">

        <Header title={title} subtitle={subtitle} />

        {/* Main content — padding keeps children away from header bottom and sidebar right edge */}
        <main className="flex-1 overflow-y-auto px-8 py-7">
          {children}
        </main>

      </div>
    </div>
  );
}