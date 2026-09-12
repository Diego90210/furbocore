import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Furbocore — Football Analytics",
  description: "Premier League analytics: transfer values, match predictions, scouting",
};

const NAV_ITEMS = [
  { href: "/transfers", label: "Transfers", color: "hover:text-blue-600" },
  { href: "/matches", label: "Matches", color: "hover:text-green-600" },
  { href: "/scouting", label: "Scouting", color: "hover:text-purple-600" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50">
        <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/60 sticky top-0 z-50">
          <nav className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between">
            <Link href="/" className="font-bold text-lg text-slate-900 tracking-tight">
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Furbo
              </span>
              core
            </Link>
            <div className="flex gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-2 text-sm font-medium text-slate-500 ${item.color} hover:bg-slate-100 rounded-lg transition-all duration-200`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </nav>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-slate-200/60 py-6 text-center text-sm text-slate-400">
          <p>Furbocore Analytics — Premier League</p>
        </footer>
      </body>
    </html>
  );
}
