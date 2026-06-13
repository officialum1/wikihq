"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiRequest, Article, authHeaders, getArticle, getStoredToken, titleToPath } from "@/lib/api";

type EditArticleFormProps = {
  title: string;
};

export default function EditArticleForm({ title }: EditArticleFormProps) {
  const router = useRouter();
  const [article, setArticle] = useState<Article | null>(null);
  const [content, setContent] = useState(`== ${title} ==\n\n`);
  const [categories, setCategories] = useState("");
  const [summary, setSummary] = useState("Updated article");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setToken(getStoredToken());
    getArticle(title)
      .then((loaded) => {
        setArticle(loaded);
        setContent(loaded.content);
        setCategories(loaded.categories.join(", "));
      })
      .catch(() => {
        setArticle(null);
      })
      .finally(() => setLoading(false));
  }, [title]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      setError("Login is required to edit articles.");
      return;
    }
    setSaving(true);
    setError(null);
    const categoryList = categories
      .split(",")
      .map((category) => category.trim())
      .filter(Boolean);

    try {
      if (article) {
        await apiRequest<Article>(`/api/article/${article.id}`, {
          method: "PUT",
          headers: authHeaders(token),
          body: JSON.stringify({
            content,
            edit_summary: summary || "Updated article",
            categories: categoryList
          })
        });
      } else {
        await apiRequest<Article>("/api/article", {
          method: "POST",
          headers: authHeaders(token),
          body: JSON.stringify({
            title,
            content,
            edit_summary: summary || "Created article",
            categories: categoryList
          })
        });
      }
      router.push(`/wiki/${titleToPath(title)}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save article");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="notice">Loading editor...</p>;
  }

  if (!token) {
    return (
      <section className="editor-shell">
        <h1>{title}</h1>
        <p className="notice">Login is required to edit articles.</p>
        <Link className="button primary" href="/auth/login">Login</Link>
      </section>
    );
  }

  return (
    <section className="editor-shell" aria-labelledby="editor-title">
      <header className="article-header">
        <div>
          <h1 id="editor-title">{article ? `Editing ${article.title}` : `Creating ${title}`}</h1>
          <p>Wikitext source</p>
        </div>
        {article ? <Link className="button" href={`/wiki/${titleToPath(article.title)}`}>Cancel</Link> : null}
      </header>
      <form className="form-stack editor-form" onSubmit={submit}>
        <label>
          Wikitext
          <textarea value={content} onChange={(event) => setContent(event.target.value)} rows={22} required />
        </label>
        <label>
          Categories
          <input value={categories} onChange={(event) => setCategories(event.target.value)} />
        </label>
        <label>
          Edit summary
          <input value={summary} onChange={(event) => setSummary(event.target.value)} maxLength={500} />
        </label>
        {error ? <p className="notice error">{error}</p> : null}
        <button className="button primary" type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save article"}
        </button>
      </form>
    </section>
  );
}
