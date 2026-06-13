import Link from "next/link";

import Sidebar from "@/components/Sidebar";
import { getArticle, getHistory, pathToTitle, titleToPath } from "@/lib/api";
import { formatDate, stripHtml } from "@/lib/format";

type HistoryPageProps = {
  params: {
    title: string;
  };
};

export default async function HistoryPage({ params }: HistoryPageProps) {
  const requestedTitle = pathToTitle(params.title);
  const article = await getArticle(requestedTitle).catch(() => null);
  const revisions = article ? await getHistory(article.id).catch(() => []) : [];

  if (!article) {
    return (
      <main className="content-page narrow">
        <h1>{requestedTitle}</h1>
        <p className="notice">No revision history exists for this title.</p>
      </main>
    );
  }

  return (
    <main className="wiki-layout">
      <Sidebar categories={article.categories} title={article.title} />
      <section className="article-view">
        <header className="article-header">
          <div>
            <h1>{article.title}: history</h1>
            <p>{revisions.length.toLocaleString()} revisions</p>
          </div>
          <Link className="button" href={`/wiki/${titleToPath(article.title)}`}>Read article</Link>
        </header>
        <div className="history-list">
          {revisions.map((revision) => (
            <article className="history-item" key={revision.id}>
              <div>
                <strong>{revision.edit_summary || "Revision"}</strong>
                <span>{formatDate(revision.created_at)} by {revision.username || "import worker"}</span>
              </div>
              <p>{stripHtml(revision.content).slice(0, 260)}</p>
            </article>
          ))}
          {revisions.length === 0 ? <p className="notice">No edits have been recorded yet.</p> : null}
        </div>
      </section>
    </main>
  );
}
