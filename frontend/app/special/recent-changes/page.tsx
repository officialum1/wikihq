import Link from "next/link";
import { Clock } from "lucide-react";

import { getRecentChanges, titleToPath } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function RecentChangesPage() {
  const changes = await getRecentChanges().catch(() => []);

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <Clock size={28} />
        <div>
          <h1>Recent Changes</h1>
          <p>Latest edits, imports, and article updates.</p>
        </div>
      </header>
      <section className="history-list">
        {changes.map((change) => (
          <article className="history-item" key={change.id}>
            <div>
              <strong>
                <Link href={`/wiki/${titleToPath(change.title)}`}>{change.title}</Link>
              </strong>
              <span>{formatDate(change.created_at)} by {change.username || "import worker"}</span>
            </div>
            <p>{change.edit_summary || "Updated article"}</p>
          </article>
        ))}
        {changes.length === 0 ? <p className="notice">No recent changes are available.</p> : null}
      </section>
    </main>
  );
}

