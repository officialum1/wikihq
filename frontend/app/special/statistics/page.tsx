import { BarChart3 } from "lucide-react";

import { getStatistics } from "@/lib/api";

export default async function StatisticsPage() {
  const stats = await getStatistics().catch(() => null);

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <BarChart3 size={28} />
        <div>
          <h1>Statistics</h1>
          <p>Wiki totals.</p>
        </div>
      </header>
      {stats ? (
        <section className="stats-grid">
          <div className="stat-panel"><span>Articles</span><strong>{stats.articles.toLocaleString()}</strong></div>
          <div className="stat-panel"><span>Users</span><strong>{stats.users.toLocaleString()}</strong></div>
          <div className="stat-panel"><span>Revisions</span><strong>{stats.revisions.toLocaleString()}</strong></div>
          <div className="stat-panel"><span>Categories</span><strong>{stats.categories.toLocaleString()}</strong></div>
          <div className="stat-panel"><span>Files</span><strong>{stats.files.toLocaleString()}</strong></div>
          <div className="stat-panel"><span>Templates</span><strong>{stats.templates.toLocaleString()}</strong></div>
        </section>
      ) : (
        <p className="notice error">Statistics are unavailable.</p>
      )}
    </main>
  );
}

