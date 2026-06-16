"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, Shield, User } from "lucide-react";

export default function UserNav() {
  const [username, setUsername] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    function syncAuthState() {
      setUsername(window.localStorage.getItem("wiki_username"));
      setRole(window.localStorage.getItem("wiki_role"));
    }

    syncAuthState();
    window.addEventListener("storage", syncAuthState);
    window.addEventListener("wiki-auth-changed", syncAuthState);
    return () => {
      window.removeEventListener("storage", syncAuthState);
      window.removeEventListener("wiki-auth-changed", syncAuthState);
    };
  }, [pathname]);

  function logout() {
    window.localStorage.removeItem("wiki_token");
    window.localStorage.removeItem("wiki_username");
    window.localStorage.removeItem("wiki_role");
    setUsername(null);
    setRole(null);
    window.dispatchEvent(new Event("wiki-auth-changed"));
  }

  if (!username) {
    return (
      <Link className="button compact" href="/auth/login">
        <User size={16} />
        Login
      </Link>
    );
  }

  return (
    <div className="user-nav">
      {role === "admin" || role === "sysop" ? (
        <Link className="icon-button" href="/admin" aria-label="Admin dashboard" title="Admin dashboard">
          <Shield size={17} />
        </Link>
      ) : null}
      <Link href="/account">{username}</Link>
      <button className="icon-button" type="button" onClick={logout} aria-label="Log out" title="Log out">
        <LogOut size={17} />
      </button>
    </div>
  );
}
