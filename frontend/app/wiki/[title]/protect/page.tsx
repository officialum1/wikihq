import Link from "next/link";
import { Shield } from "lucide-react";

import Sidebar from "@/components/Sidebar";
import ProtectForm from "@/components/ProtectForm";
import { getArticle, getPageProtection, pathToTitle, titleToPath } from "@/lib/api";
import { formatDate } from "@/lib/format";

type ProtectionPageProps = {
  params: {
    title: string;
  };
};

export default async function ProtectionPage({ params }: ProtectionPageProps) {
  const requestedTitle = pathToTitle(params.title);
  const article = await getArticle(requestedTitle).catch(() => null);
  const protection = article ? await getPageProtection(article.id).catch(() => null) : null;

  if (!article) {
    return (
      <main className="content-page narrow">
        <h1>{requestedTitle}: protection</h1>
        <p className="notice">Protection information is unavailable for this title.</p>
      </main>
    );
  }

  return (
    <main className="wiki-layout">
      <Sidebar categories={article.categories} title={article.title} />
      <section className="article-view">
        <header className="article-header">
          <div>
            <h1>{article.title}: protection</h1>
            <p>Protection status</p>
          </div>
          <Link className="button" href={`/wiki/${titleToPath(article.title)}`}>Read article</Link>
        </header>
        {protection ? (
          <section className="stats-grid">
            <div className="stat-panel">
              <span>Level</span>
              <strong>{protection.level}</strong>
            </div>
            <div className="stat-panel">
              <span>Reason</span>
              <strong>{protection.reason || "No reason"}</strong>
            </div>
            <div className="stat-panel">
              <span>Created</span>
              <strong>{formatDate(protection.created_at)}</strong>
            </div>
            <div className="stat-panel">
              <span>Expires</span>
              <strong>{protection.expires_at ? formatDate(protection.expires_at) : "Indefinite"}</strong>
            </div>
          </section>
        ) : (
          <p className="notice">
            <Shield size={16} />
            This page is not protected.
          </p>
        )}
        <ProtectForm articleId={article.id} currentLevel={protection?.level} />
      </section>
    </main>
  );
}

