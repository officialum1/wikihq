import Link from "next/link";
import { BadgeCheck } from "lucide-react";

import { getPatrolQueue, titleToPath } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function PatrolPage() {
  const items = await getPatrolQueue().catch(() => []);

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <BadgeCheck size={28} />
        <div>
          <h1>Patrol</h1>
          <p>Recent edits review queue.</p>
        </div>
      </header>
      <section className="history-list">
        {items.map((item) => (
          <article className="history-item" key={item.revision_id}>
            <div>
              <strong>
                <Link href={`/wiki/${titleToPath(item.title)}`}>{item.title}</Link>
              </strong>
              <span>{item.status} · {formatDate(item.created_at)}</span>
            </div>
            <p>{item.edit_summary || "Updated article"} by {item.username || "import worker"}</p>
          </article>
        ))}
        {items.length === 0 ? <p className="notice">No patrol items are available.</p> : null}
      </section>
    </main>
  );
}

