import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI 食譜檢索與創作小助手',
  description: '依據現有食材，為你檢索真實網路料理或生成獨特 AI 創意食譜！',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-TW">
      <body className="min-h-screen flex flex-col bg-stone-50 text-stone-800 antialiased selection:bg-orange-200">
        {children}
      </body>
    </html>
  );
}
