import Sidebar from './Sidebar';
import Header from './Header';

export default function Shell({ children, title, subtitle }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header title={title} subtitle={subtitle} />
        <main className="flex-1 p-6 animate-[fadeUp_0.4s_var(--t-slow)_both]">
          {children}
        </main>
      </div>
    </div>
  );
}