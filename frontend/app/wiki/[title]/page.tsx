import Link from "next/link";
import { Edit3, History } from "lucide-react";

import Sidebar from "@/components/Sidebar";
import TableOfContents from "@/components/TableOfContents";
import WatchButton from "@/components/WatchButton";
import { getArticle, getCategoryMembers, pathToTitle, titleToPath } from "@/lib/api";
import { formatDate } from "@/lib/format";

type ArticlePageProps = {
  params: {
    title: string;
  };
};

import { Metadata } from "next";

export async function generateMetadata({ params }: ArticlePageProps): Promise<Metadata> {
  const requestedTitle = pathToTitle(params.title);
  const article = await getArticle(requestedTitle).catch(() => null);

  if (!article) {
    return {
      title: `${requestedTitle} - WikiHQ`,
      description: `Create the ${requestedTitle} article on WikiHQ.`
    };
  }

  // Extract a short description from the HTML content
  const textContent = article.html_content.replace(/<[^>]+>/g, "").slice(0, 160);
  
  return {
    title: `${article.title} - WikiHQ`,
    description: textContent || `Read about ${article.title} on WikiHQ.`,
    openGraph: {
      title: `${article.title} - WikiHQ`,
      description: textContent || `Read about ${article.title} on WikiHQ.`,
      siteName: "WikiHQ",
      type: "article",
      publishedTime: article.created_at,
      modifiedTime: article.updated_at,
    }
  };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const requestedTitle = pathToTitle(params.title);
  const article = await getArticle(requestedTitle).catch(() => null);
  
  let categoryMembers: any[] = [];
  if (article && article.title.startsWith("Category:")) {
    categoryMembers = await getCategoryMembers(article.title).catch(() => []);
  }

  if (!article) {
    return (
      <main className="content-page narrow">
        <h1>{requestedTitle}</h1>
        <p className="notice">This article does not exist yet.</p>
        <Link className="button primary" href={`/wiki/${titleToPath(requestedTitle)}/edit`}>
          Create article
        </Link>
      </main>
    );
  }

  return (
    <main className="wiki-layout">
      <Sidebar categories={article.categories} interlanguageLinks={article.interlanguage_links} title={article.title} />
      <article className="article-view">
        <header className="article-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h1>{article.title}</h1>
            <WatchButton articleId={article.id} />
          </div>
          <div>
            <p>{article.word_count.toLocaleString()} words updated {formatDate(article.updated_at)}</p>
          </div>
          <div className="article-actions">
            <Link className="button" href={`/wiki/${titleToPath(article.title)}/edit`}>
              <Edit3 size={16} />
              Edit
            </Link>
            <Link className="button" href={`/wiki/${titleToPath(article.title)}/history`}>
              <History size={16} />
              History
            </Link>
          </div>
        </header>
        <div className="article-columns">
          <div className="article-body" dir="auto" dangerouslySetInnerHTML={{ __html: article.html_content }} />
          <TableOfContents html={article.html_content} />
        </div>
        
        {categoryMembers.length > 0 && (
          <section className="category-members" style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #ccc' }}>
            <h2>Pages in category "{article.title.replace("Category:", "").trim()}"</h2>
            <ul>
              {categoryMembers.map(member => (
                <li key={member.id}>
                  <Link href={`/wiki/${titleToPath(member.title)}`}>{member.title}</Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </article>
    </main>
  );
}
