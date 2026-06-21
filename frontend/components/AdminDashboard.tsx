"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Shield } from "lucide-react";

import { getMe, getStatistics, getStoredToken, type Statistics, type UserProfile } from "@/lib/api";

export default function AdminDashboard() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<Statistics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setError("Admin login is required.");
      return;
    }
    Promise.all([getMe(token), getStatistics()])
      .then(([user, loadedStats]) => {
        if (user.role !== "admin" && user.role !== "sysop") {
          setError("Admin role required.");
          return;
        }
        setProfile(user);
        setStats(loadedStats);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load admin dashboard"));
  }, []);

  if (error) {
    return (
      <section className="auth-panel">
        <h1>Admin</h1>
        <p className="notice error">{error}</p>
        <Link className="button primary" href="/admin/login">Admin login</Link>
      </section>
    );
  }

  if (!profile || !stats) {
    return <p className="notice">Loading admin dashboard...</p>;
  }

  return (
    <section className="admin-shell">
      <header className="section-heading">
        <Shield size={30} />
        <div>
          <h1>Admin Dashboard</h1>
          <p>Signed in as {profile.username}</p>
        </div>
      </header>
      <section className="stats-grid">
        <div className="stat-panel"><span>Articles</span><strong>{stats.articles.toLocaleString()}</strong></div>
        <div className="stat-panel"><span>Users</span><strong>{stats.users.toLocaleString()}</strong></div>
        <div className="stat-panel"><span>Revisions</span><strong>{stats.revisions.toLocaleString()}</strong></div>
        <div className="stat-panel"><span>Categories</span><strong>{stats.categories.toLocaleString()}</strong></div>
        <div className="stat-panel"><span>Files</span><strong>{stats.files.toLocaleString()}</strong></div>
        <div className="stat-panel"><span>Templates</span><strong>{stats.templates.toLocaleString()}</strong></div>
      </section>
      <nav className="admin-grid" aria-label="Admin tools">
        <Link className="result-item" href="/special/recent-changes"><h3>Recent changes</h3><p>Review latest edits.</p></Link>
        <Link className="result-item" href="/special/patrol"><h3>Patrol</h3><p>Moderation queue.</p></Link>
        <Link className="result-item" href="/special/files"><h3>Files</h3><p>Media records.</p></Link>
        <Link className="result-item" href="/special/templates"><h3>Templates</h3><p>Reusable wiki snippets.</p></Link>
        <Link className="result-item" href="/special/redirects"><h3>Redirects</h3><p>Redirect management.</p></Link>
      </nav>
    </section>
  );
}

