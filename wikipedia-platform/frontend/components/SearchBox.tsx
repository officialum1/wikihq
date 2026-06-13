"use client";

import { FormEvent, useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import Link from "next/link";
import { searchSuggest, titleToPath } from "@/lib/api";

type SearchBoxProps = {
  initialQuery?: string;
  autoFocus?: boolean;
};

export default function SearchBox({ initialQuery = "", autoFocus = false }: SearchBoxProps) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const router = useRouter();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const debounce = setTimeout(async () => {
      if (query.trim().length >= 2) {
        try {
          const results = await searchSuggest(query);
          setSuggestions(results);
          setShowSuggestions(true);
        } catch {
          setSuggestions([]);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(debounce);
  }, [query]);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setShowSuggestions(false);
    const trimmed = query.trim();
    if (trimmed) {
      router.push(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  }

  return (
    <form className="search-box" onSubmit={onSubmit}>
      <label htmlFor="site-search">Search</label>
      <div ref={wrapperRef} style={{ position: 'relative' }}>
        <Search size={20} aria-hidden="true" />
        <input
          id="site-search"
          name="q"
          value={query}
          autoFocus={autoFocus}
          autoComplete="off"
          onFocus={() => { if (suggestions.length > 0) setShowSuggestions(true); }}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button type="submit" aria-label="Search">
          <Search size={18} />
        </button>

        {showSuggestions && suggestions.length > 0 && (
          <div style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            background: 'white',
            border: '1px solid #ccc',
            borderTop: 'none',
            zIndex: 1000,
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
          }}>
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {suggestions.map((suggestion, index) => (
                <li key={index}>
                  <Link 
                    href={`/wiki/${titleToPath(suggestion)}`}
                    style={{
                      display: 'block',
                      padding: '8px 12px',
                      textDecoration: 'none',
                      color: 'black',
                      borderBottom: index < suggestions.length - 1 ? '1px solid #eee' : 'none'
                    }}
                    onClick={() => {
                      setQuery(suggestion);
                      setShowSuggestions(false);
                    }}
                  >
                    {suggestion}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </form>
  );
}
