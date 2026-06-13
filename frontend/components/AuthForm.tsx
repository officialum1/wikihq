"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { apiRequest, AuthToken } from "@/lib/api";

type AuthFormProps = {
  mode: "login" | "register" | "admin";
};

export default function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const isRegister = mode === "register";
  const isAdmin = mode === "admin";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = isRegister
        ? { username, email, password }
        : { username_or_email: username, password };
      const endpoint = isAdmin ? "/api/auth/admin/login" : `/api/auth/${mode}`;
      const token = await apiRequest<AuthToken>(endpoint, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      window.localStorage.setItem("wiki_token", token.access_token);
      window.localStorage.setItem("wiki_username", token.username);
      window.localStorage.setItem("wiki_role", token.role);
      
      await fetch("/api/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: token.access_token })
      });

      window.dispatchEvent(new Event("wiki-auth-changed"));
      router.push(isAdmin || token.role === "admin" ? "/admin" : "/account");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="auth-panel" aria-labelledby="auth-title">
      <h1 id="auth-title">{isRegister ? "Create account" : isAdmin ? "Admin login" : "Login"}</h1>
      <form className="form-stack" onSubmit={submit}>
        <label>
          {isRegister ? "Username" : "Username or email"}
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            minLength={3}
            maxLength={255}
            required
          />
        </label>
        {isRegister ? (
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
        ) : null}
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            maxLength={128}
            required
          />
        </label>
        {error ? <p className="notice error">{error}</p> : null}
        <button className="button primary" type="submit" disabled={saving}>
          {saving ? "Working..." : isRegister ? "Create account" : isAdmin ? "Admin login" : "Login"}
        </button>
      </form>
      <p className="auth-switch">
        {isAdmin ? (
          <>
            User login? <Link href="/auth/login">Login</Link>
          </>
        ) : isRegister ? (
          <>
            Already have an account? <Link href="/auth/login">Login</Link>
          </>
        ) : (
          <>
            Need an account? <Link href="/auth/register">Register</Link>
            {" | "}
            <Link href="/admin/login">Admin login</Link>
          </>
        )}
      </p>
    </section>
  );
}
