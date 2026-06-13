import Link from "next/link";
import { Link2 } from "lucide-react";

import Sidebar from "@/components/Sidebar";
import { getArticle, getBacklinks, pathToTitle, titleToPath } from "@/lib/api";

type BacklinksPageProps = {
  params: {
    title: string;
  };
};

export default async function BacklinksPage({ params }: BacklinksPageProps) {
  const requestedTitle = pathToTitle(params.title);
  const article = await getArticle(requestedTitle).catch(() => null);
  const backlinks = article ? await getBacklinks(article.id).catch(() => []) : [];

  if (!article) {
    return (
      <main className="content-page narrow">
        <h1>{requestedTitle}: backlinks</h1>
        <p className="notice">Backlinks are unavailable for this title.</p>
      </main>
    );
  }

  return (
    <main className="wiki-layout">
      <Sidebar categories={article.categories} title={article.title} />
      <section className="article-view">
        <header className="article-header">
          <div>
            <h1>What links here</h1>
            <p>{article.title}</p>
          </div>
          <Link className="button" href={`/wiki/${titleToPath(article.title)}`}>Read article</Link>
        </header>
        <section className="result-list">
          {backlinks.map((backlink) => (
            <article className="result-item" key={`${backlink.source}-${backlink.id}`}>
              <h3>
                <Link href={`/wiki/${titleToPath(backlink.title)}`}>{backlink.title}</Link>
              </h3>
              <p>
                <Link2 size={15} />
                {backlink.source}
              </p>
            </article>
          ))}
          {backlinks.length === 0 ? <p className="notice">No backlinks were found.</p> : null}
        </section>
      </section>
    </main>
  );
}

