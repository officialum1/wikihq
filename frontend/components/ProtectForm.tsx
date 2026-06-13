"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { updateProtection, deleteProtection, getStoredToken } from "@/lib/api";

export default function ProtectForm({ articleId, currentLevel }: { articleId: number; currentLevel?: string }) {
  const router = useRouter();
  const [level, setLevel] = useState(currentLevel || "autoconfirmed");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleProtect = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const token = getStoredToken();
    if (!token) {
      setError("You must be logged in as an administrator.");
      setLoading(false);
      return;
    }

    try {
      await updateProtection(articleId, level, reason, token);
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to protect page.");
    } finally {
      setLoading(false);
    }
  };

  const handleUnprotect = async () => {
    if (!confirm("Are you sure you want to unprotect this page?")) return;
    setError(null);
    setLoading(true);

    const token = getStoredToken();
    if (!token) return;

    try {
      await deleteProtection(articleId, token);
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to unprotect page.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleProtect} className="edit-form" style={{ marginTop: "2rem" }}>
      <h3>Change Protection Level</h3>
      <p>Only administrators can modify page protection.</p>
      {error && <div className="error-message">{error}</div>}
      <div className="form-group">
        <label>Protection Level</label>
        <select value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="autoconfirmed">Semi-protection (Registered users only)</option>
          <option value="sysop">Full protection (Administrators only)</option>
        </select>
      </div>
      <div className="form-group">
        <label>Reason</label>
        <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why is this page being protected?" />
      </div>
      <div className="form-actions">
        <button type="submit" disabled={loading} className="btn-primary">
          Update Protection
        </button>
        {currentLevel && (
          <button type="button" onClick={handleUnprotect} disabled={loading} className="button" style={{ marginLeft: "1rem" }}>
            Unprotect Page
          </button>
        )}
      </div>
    </form>
  );
}
