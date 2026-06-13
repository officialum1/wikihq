import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { BookOpen, Gauge, Home, ListTree, Search } from "lucide-react";

import ThemeToggle from "@/components/ThemeToggle";
import UserNav from "@/components/UserNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Wikipedia Platform",
  description: "A Wikipedia mirror and editable wiki platform"
};

function ThemeScript() {
  const script = `
    (() => {
      const stored = localStorage.getItem("theme");
      const dark = stored ? stored === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.classList.toggle("dark", dark);
    })();
  `;
  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeScript />
        <header className="topbar">
          <Link className="brand" href="/">
            <span className="brand-mark">W</span>
            <span>Wikipedia Platform</span>
          </Link>
          <nav className="topnav" aria-label="Primary">
            <Link href="/">
              <Home size={17} />
              Home
            </Link>
            <Link href="/search">
              <Search size={17} />
              Search
            </Link>
            <Link href="/admin/progress">
              <Gauge size={17} />
              Progress
            </Link>
            <Link href="/special">
              <ListTree size={17} />
              Special
            </Link>
            <Link href="/wiki/Main_Page">
              <BookOpen size={17} />
              Main Page
            </Link>
          </nav>
          <div className="top-actions">
            <ThemeToggle />
            <UserNav />
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
