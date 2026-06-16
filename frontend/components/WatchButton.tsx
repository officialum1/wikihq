"use client";

import { useState, useEffect } from "react";
import { Star } from "lucide-react";
import { addToWatchlist, removeFromWatchlist, getWatchlist, getStoredToken } from "@/lib/api";

export default function WatchButton({ articleId }: { articleId: number }) {
  const [isWatched, setIsWatched] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setLoading(false);
      return;
    }
    
    getWatchlist(token).then((list) => {
      setIsWatched(list.some(item => item.article_id === articleId));
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });
  }, [articleId]);

  const toggleWatch = async () => {
    const token = getStoredToken();
    if (!token) {
      alert("Please log in to watch this article.");
      return;
    }
    
    setLoading(true);
    try {
      if (isWatched) {
        await removeFromWatchlist(articleId, token);
        setIsWatched(false);
      } else {
        await addToWatchlist(articleId, token);
        setIsWatched(true);
      }
    } catch (err: any) {
      alert(err.message || "Failed to toggle watchlist status.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button 
      onClick={toggleWatch} 
      disabled={loading} 
      title={isWatched ? "Unwatch this page" : "Watch this page"}
      className="button"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0.4rem',
        background: 'transparent',
        border: 'none',
        cursor: loading ? 'not-allowed' : 'pointer',
        color: isWatched ? '#e6b800' : '#888'
      }}
    >
      <Star size={20} fill={isWatched ? "#e6b800" : "none"} />
    </button>
  );
}
