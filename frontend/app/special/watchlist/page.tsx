"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Eye } from "lucide-react";

import { getWatchlist, titleToPath, WatchlistItem, getStoredToken } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setLoading(false);
      return;
    }

    getWatchlist(token).then((data) => {
      setItems(data);
      setLoading(false);
    }).catch((err: any) => {
      setError(err.message || "Failed to load watchlist.");
      setLoading(false);
    });
  }, []);

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <Eye size={28} />
        <div>
          <h1>Watchlist</h1>
          <p>Followed pages.</p>
        </div>
      </header>
      
      {error && <div className="error-message">{error}</div>}
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <section className="result-list">
          {items.map((item) => (
            <article className="result-item" key={item.id}>
              <h3>
                <Link href={`/wiki/${titleToPath(item.title)}`}>{item.title}</Link>
              </h3>
              <span>Watched {formatDate(item.created_at)}</span>
            </article>
          ))}
          {items.length === 0 ? <p className="notice">Your watchlist is empty or login is required.</p> : null}
        </section>
      )}
    </main>
  );
}
