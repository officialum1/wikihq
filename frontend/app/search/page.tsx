import Link from "next/link";

import SearchBox from "@/components/SearchBox";
import { getArticle, searchArticles, titleToPath } from "@/lib/api";
import { formatDate, stripHtml } from "@/lib/format";

type SearchPageProps = {
  searchParams: {
    q?: string;
    page?: string;
  };
};

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const query = typeof searchParams.q === "string" ? searchParams.q : "";
  const trimmedQuery = query.trim();
  const page = Math.max(Number(searchParams.page || "1"), 1);
  let data: Awaited<ReturnType<typeof searchArticles>> | null = null;
  let exactArticleExists = false;

  if (trimmedQuery) {
    [data, exactArticleExists] = await Promise.all([
      searchArticles(trimmedQuery, page).catch(() => null),
      getArticle(trimmedQuery).then(() => true).catch(() => false)
    ]);
  }

  const totalPages = data ? Math.max(Math.ceil(data.total / data.page_size), 1) : 1;
  const createHref = `/wiki/${titleToPath(trimmedQuery)}/edit`;
  const shouldOfferCreate = Boolean(trimmedQuery && data && !exactArticleExists);

  return (
    <main className="content-page narrow">
      <h1>Search</h1>
      <SearchBox initialQuery={query} />
      {query && data === null ? (
        <p className="notice error">Search is unavailable right now.</p>
      ) : null}
      {data ? (
        <section className="result-list" aria-label="Search results">
          {shouldOfferCreate ? (
            <aside className="create-search-prompt" aria-label="Create missing article">
              <div>
                <strong>Create the page "{trimmedQuery}"</strong>
                <p>No article with this exact title exists yet.</p>
              </div>
              <Link className="button primary" href={createHref}>Create article</Link>
            </aside>
          ) : null}
          <p className="muted">{data.total.toLocaleString()} results for {data.query}</p>
          {data.results.map((result) => (
            <article className="result-item" key={result.id}>
              <h2>
                <Link href={`/wiki/${titleToPath(result.title)}`}>{result.title}</Link>
              </h2>
              <p>{stripHtml(result.snippet)}</p>
              <span>{result.word_count.toLocaleString()} words updated {formatDate(result.updated_at)}</span>
            </article>
          ))}
          {data.results.length === 0 ? (
            <div className="empty-state">
              <p>No matching articles were found.</p>
            </div>
          ) : null}
          {totalPages > 1 ? (
            <nav className="pagination" aria-label="Search pages">
              <Link aria-disabled={page <= 1} href={`/search?q=${encodeURIComponent(query)}&page=${page - 1}`}>
                Previous
              </Link>
              <span>Page {page} of {totalPages}</span>
              <Link aria-disabled={page >= totalPages} href={`/search?q=${encodeURIComponent(query)}&page=${page + 1}`}>
                Next
              </Link>
            </nav>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
