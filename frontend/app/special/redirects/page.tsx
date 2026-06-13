import Link from "next/link";
import { CornerDownRight } from "lucide-react";

import { getRedirects, titleToPath } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function RedirectsPage() {
  const redirects = await getRedirects().catch(() => []);

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <CornerDownRight size={28} />
        <div>
          <h1>Redirects</h1>
          <p>Redirect source and target pages.</p>
        </div>
      </header>
      <section className="history-list">
        {redirects.map((redirect) => (
          <article className="history-item" key={redirect.id}>
            <div>
              <strong>{redirect.source_title}</strong>
              <span>{formatDate(redirect.created_at)}</span>
            </div>
            <p>
              <Link href={`/wiki/${titleToPath(redirect.target_title)}`}>{redirect.target_title}</Link>
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}

