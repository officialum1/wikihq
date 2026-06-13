import Link from "next/link";
import { MessageSquare } from "lucide-react";

import Sidebar from "@/components/Sidebar";
import TalkForm from "@/components/TalkForm";
import { getArticle, getTalkMessages, pathToTitle, titleToPath } from "@/lib/api";
import { formatDate } from "@/lib/format";

type TalkPageProps = {
  params: {
    title: string;
  };
};

export default async function TalkPage({ params }: TalkPageProps) {
  const requestedTitle = pathToTitle(params.title);
  const article = await getArticle(requestedTitle).catch(() => null);
  const messages = article ? await getTalkMessages(article.id).catch(() => []) : [];

  if (!article) {
    return (
      <main className="content-page narrow">
        <h1>{requestedTitle}: discussion</h1>
        <p className="notice">Discussion is unavailable for this title.</p>
      </main>
    );
  }

  return (
    <main className="wiki-layout">
      <Sidebar categories={article.categories} title={article.title} />
      <section className="article-view">
        <header className="article-header">
          <div>
            <h1>{article.title}: discussion</h1>
            <p>Talk page</p>
          </div>
          <Link className="button" href={`/wiki/${titleToPath(article.title)}`}>
            Read article
          </Link>
        </header>
        <section className="history-list">
          {messages.map((message) => (
            <article className="history-item" key={message.id}>
              <div>
                <strong>
                  <MessageSquare size={16} />
                  {message.username || "anonymous"}
                </strong>
                <span>{formatDate(message.created_at)}</span>
              </div>
              <p>{message.body}</p>
            </article>
          ))}
          {messages.length === 0 ? <p className="notice">No discussion messages yet.</p> : null}
          <TalkForm articleId={article.id} />
        </section>
      </section>
    </main>
  );
}

