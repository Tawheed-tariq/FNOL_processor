import './globals.css';

export const metadata = {
  title: 'FNOL · Claims Intelligence Platform',
  description: 'AI-powered First Notice of Loss document processing and claims routing system.',
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}