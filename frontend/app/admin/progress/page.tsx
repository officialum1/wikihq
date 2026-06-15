import { Gauge } from "lucide-react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { getProgress } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function ProgressPage() {
  const token = cookies().get("token");
  if (!token?.value) {
    redirect("/admin/login");
  }

  const progress = await getProgress().catch(() => null);

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <Gauge size={28} />
        <div>
          <h1>Import Progress</h1>
          <p>Worker status and latest imported page marker.</p>
        </div>
      </header>
      {progress ? (
        <section className="stats-grid">
          <div className="stat-panel">
            <span>Status</span>
            <strong>{progress.status}</strong>
          </div>
          {progress.message && (
            <div className="stat-panel" style={{ gridColumn: "1 / -1" }}>
              <span>Current Activity</span>
              <strong>{progress.message}</strong>
            </div>
          )}
          <div className="stat-panel">
            <span>Total imported</span>
            <strong>{progress.total_imported.toLocaleString()}</strong>
          </div>
          <div className="stat-panel">
            <span>Last page ID</span>
            <strong>{progress.last_page_id.toLocaleString()}</strong>
          </div>
          <div className="stat-panel">
            <span>Updated</span>
            <strong>{formatDate(progress.updated_at)}</strong>
          </div>
        </section>
      ) : (
        <p className="notice error">The import progress endpoint is unavailable.</p>
      )}
    </main>
  );
}
