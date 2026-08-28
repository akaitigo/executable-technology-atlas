import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'),
  title: '実行可能技術アトラス | Executable Technology Atlas',
  description: '97 Subject Atlasの固定Release、Coverage、Evidence、Skill、Completion Certificateを検証・探索する日本語Portal。',
  openGraph: {
    title: '実行可能技術アトラス',
    description: '固定Releaseを横断する検証済みRead Model',
    images: [{ url: '/og.png', width: 1729, height: 910, alt: '実行可能技術アトラス — 固定Releaseを横断する検証済みRead Model' }],
    locale: 'ja_JP',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: '実行可能技術アトラス',
    description: '固定Releaseを横断する検証済みRead Model',
    images: ['/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ja"><body>{children}</body></html>;
}
