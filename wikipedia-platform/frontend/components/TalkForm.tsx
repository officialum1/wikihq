"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createTalkMessage, getStoredToken } from "@/lib/api";

export default function TalkForm({ articleId }: { articleId: number }) {
  const router = useRouter();
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const token = getStoredToken();
    if (!token) {
      setError("You must be logged in to post a message.");
      setLoading(false);
      return;
    }

    if (!body.trim()) {
      setError("Message cannot be empty.");
      setLoading(false);
      return;
    }

    try {
      await createTalkMessage(articleId, body, token);
      setBody("");
      router.refresh(); // Refresh the page to show the new message
    } catch (err: any) {
      setError(err.message || "Failed to post message.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="edit-form" style={{ marginTop: '2rem' }}>
      <h3>Add a message</h3>
      {error && <div className="error-message">{error}</div>}
      <div className="form-group">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={4}
          placeholder="Write your discussion message here..."
          required
        />
      </div>
      <div className="form-actions">
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? "Posting..." : "Post Message"}
        </button>
      </div>
    </form>
  );
}
