import Link from "next/link";

import Sidebar from "@/components/Sidebar";
import { getArticle, getPageInfo, pathToTitle, titleToPath } from "@/lib/api";
import { formatDate } from "@/lib/format";

type InfoPageProps = {
  params: {
    title: string;
  };
};

export default async function PageInfoPage({ params }: InfoPageProps) {
  const requestedTitle = pathToTitle(params.title);
  const article = await getArticle(requestedTitle).catch(() => null);
  const info = article ? await getPageInfo(article.id).catch(() => null) : null;

  if (!article || !info) {
    return (
      <main className="content-page narrow">
        <h1>{requestedTitle}</h1>
        <p className="notice">Page information is unavailable for this title.</p>
      </main>
    );
  }

  return (
    <main className="wiki-layout">
      <Sidebar categories={info.categories} title={info.title} />
      <section className="article-view">
        <header className="article-header">
          <div>
            <h1>{info.title}: page information</h1>
            <p>Metadata and maintenance details for this article.</p>
          </div>
          <Link className="button" href={`/wiki/${titleToPath(info.title)}`}>Read article</Link>
        </header>
        <section className="stats-grid">
          <div className="stat-panel">
            <span>Page ID</span>
            <strong>{info.page_id ?? info.id}</strong>
          </div>
          <div className="stat-panel">
            <span>Revisions</span>
            <strong>{info.revision_count.toLocaleString()}</strong>
          </div>
          <div className="stat-panel">
            <span>Words</span>
            <strong>{info.word_count.toLocaleString()}</strong>
          </div>
          <div className="stat-panel">
            <span>Origin</span>
            <strong>{info.is_user_created ? "User page" : "Imported"}</strong>
          </div>
          <div className="stat-panel">
            <span>Created</span>
            <strong>{formatDate(info.created_at)}</strong>
          </div>
          <div className="stat-panel">
            <span>Updated</span>
            <strong>{formatDate(info.updated_at)}</strong>
          </div>
        </section>
      </section>
    </main>
  );
}

