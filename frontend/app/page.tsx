import Link from "next/link";

import SearchBox from "@/components/SearchBox";

export default function HomePage() {
  return (
    <main className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="wiki-emblem" aria-hidden="true">W</div>
        <h1 id="home-title">WikiHQ</h1>
        <p>The free encyclopedia mirror.</p>
        <SearchBox autoFocus />
        <div className="home-links">
          <Link href="/wiki/Main_Page">Main Page</Link>
          <Link href="/admin/progress">Import Progress</Link>
          <Link href="/auth/register">Create Account</Link>
        </div>
      </section>
    </main>
  );
}
