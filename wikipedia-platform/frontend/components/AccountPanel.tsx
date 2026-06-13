"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Shield, User } from "lucide-react";

import { getMe, getStoredToken, type UserProfile } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default function AccountPanel() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setError("Login is required.");
      return;
    }
    getMe(token)
      .then(setProfile)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load account"));
  }, []);

  if (error) {
    return (
      <section className="auth-panel">
        <h1>Account</h1>
        <p className="notice">{error}</p>
        <Link className="button primary" href="/auth/login">Login</Link>
      </section>
    );
  }

  if (!profile) {
    return <p className="notice">Loading account...</p>;
  }

  return (
    <section className="auth-panel">
      <header className="section-heading">
        <User size={28} />
        <div>
          <h1>{profile.username}</h1>
          <p>{profile.email}</p>
        </div>
      </header>
      <section className="stats-grid">
        <div className="stat-panel">
          <span>Role</span>
          <strong>{profile.role}</strong>
        </div>
        <div className="stat-panel">
          <span>Created</span>
          <strong>{formatDate(profile.created_at)}</strong>
        </div>
      </section>
      <div className="account-actions">
        <Link className="button" href="/special/watchlist">Watchlist</Link>
        <Link className="button" href="/wiki/Demo_Article/edit">Create or edit article</Link>
        {profile.role === "admin" || profile.role === "sysop" ? (
          <Link className="button primary" href="/admin">
            <Shield size={16} />
            Admin dashboard
          </Link>
        ) : null}
      </div>
    </section>
  );
}

