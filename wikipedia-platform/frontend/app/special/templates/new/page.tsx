"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Braces } from "lucide-react";
import { createTemplate, getStoredToken } from "@/lib/api";

export default function NewTemplatePage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [content, setContent] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const token = getStoredToken();
    if (!token) {
      setError("You must be logged in to create a template.");
      setLoading(false);
      return;
    }

    try {
      await createTemplate(name, content, description, token);
      router.push("/special/templates");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to create template.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <Braces size={28} />
        <div>
          <h1>Create Template</h1>
          <p>Add a new reusable wiki snippet.</p>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="edit-form">
        <div className="form-group">
          <label htmlFor="name">Template Name</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g., Infobox"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <input
            id="description"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            placeholder="What does this template do?"
          />
        </div>

        <div className="form-group">
          <label htmlFor="content">Template Content (Wikitext)</label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            rows={10}
            placeholder="Template wikitext goes here. Use {{{1}}} for parameters."
          />
        </div>

        <div className="form-actions">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Saving..." : "Save Template"}
          </button>
        </div>
      </form>
    </main>
  );
}
