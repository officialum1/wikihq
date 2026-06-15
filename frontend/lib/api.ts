const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const INTERNAL_API_HOSTPORT = process.env.INTERNAL_API_HOSTPORT;
const SERVER_API_URL =
  process.env.INTERNAL_API_URL ||
  (INTERNAL_API_HOSTPORT ? `http://${INTERNAL_API_HOSTPORT}` : PUBLIC_API_URL);

export const API_URL = typeof window === "undefined" ? SERVER_API_URL : PUBLIC_API_URL;

export type Article = {
  id: number;
  page_id: number | null;
  title: string;
  content: string;
  html_content: string;
  word_count: number;
  is_user_created: boolean;
  categories: string[];
  interlanguage_links: Record<string, string>;
  created_at: string;
  updated_at: string;
};

export type Revision = {
  id: number;
  article_id: number;
  user_id: number | null;
  username: string | null;
  content: string;
  edit_summary: string;
  created_at: string;
};

export type Progress = {
  id: number;
  last_page_id: number;
  total_imported: number;
  status: string;
  message?: string;
  updated_at: string;
};

export type SearchResult = {
  id: number;
  title: string;
  snippet: string;
  word_count: number;
  updated_at: string;
};

export type SearchResponse = {
  query: string;
  page: number;
  page_size: number;
  total: number;
  results: SearchResult[];
};

export type RecentChange = {
  id: number;
  article_id: number;
  title: string;
  username: string | null;
  edit_summary: string;
  created_at: string;
};

export type PageInfo = {
  id: number;
  page_id: number | null;
  title: string;
  word_count: number;
  is_user_created: boolean;
  revision_count: number;
  categories: string[];
  created_at: string;
  updated_at: string;
};

export type SpecialPage = {
  title: string;
  path: string;
  description: string;
  section: string;
};

export type NamespaceInfo = {
  id: number;
  name: string;
  slug: string;
  description: string;
};

export type TalkMessage = {
  id: number;
  article_id: number;
  username: string | null;
  body: string;
  created_at: string;
};

export type WatchlistItem = {
  id: number;
  article_id: number;
  title: string;
  created_at: string;
};

export type PageProtection = {
  id: number;
  article_id: number;
  title: string;
  level: string;
  reason: string;
  expires_at: string | null;
  created_at: string;
};

export type Backlink = {
  id: number;
  title: string;
  source: string;
};

export type RedirectItem = {
  id: number;
  source_title: string;
  target_title: string;
  created_at: string;
};

export type FileAsset = {
  id: number;
  title: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  description: string;
  uploader: string | null;
  created_at: string;
};

export type TemplateItem = {
  id: number;
  name: string;
  content: string;
  description: string;
  created_at: string;
  updated_at: string;
};

export type PatrolItem = {
  revision_id: number;
  article_id: number;
  title: string;
  username: string | null;
  status: string;
  edit_summary: string;
  created_at: string;
};

export type Statistics = {
  articles: number;
  users: number;
  revisions: number;
  categories: number;
  files: number;
  templates: number;
};

export type AuthToken = {
  access_token: string;
  token_type: "bearer";
  username: string;
  role: string;
};

export type UserProfile = {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
};

export function titleToPath(title: string): string {
  return encodeURIComponent(title.trim().replaceAll(" ", "_"));
}

export function pathToTitle(pathTitle: string): string {
  return decodeURIComponent(pathTitle).replaceAll("_", " ");
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem("wiki_token");
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: init.cache ?? "no-store"
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      message = response.statusText;
    }
    throw new Error(message || "Request failed");
  }

  return response.json() as Promise<T>;
}

export function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`
  };
}

export function getMe(token: string): Promise<UserProfile> {
  return apiRequest<UserProfile>("/api/auth/me", {
    headers: authHeaders(token)
  });
}

export function getArticle(title: string): Promise<Article> {
  return apiRequest<Article>(`/api/article/${titleToPath(title)}`);
}

export function searchArticles(query: string, page = 1, pageSize = 20): Promise<SearchResponse> {
  return apiRequest<SearchResponse>(`/api/search?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`);
}

export function searchSuggest(query: string): Promise<string[]> {
  return apiRequest<string[]>(`/api/search/suggest?q=${encodeURIComponent(query)}`);
}

export function getProgress(): Promise<Progress> {
  return apiRequest<Progress>("/api/progress");
}

export function getHistory(articleId: number): Promise<Revision[]> {
  return apiRequest<Revision[]>(`/api/article/${articleId}/history`);
}

export function getRecentChanges(page = 1): Promise<RecentChange[]> {
  return apiRequest<RecentChange[]>(`/api/recent-changes?page=${page}`);
}

export function getRandomArticle(): Promise<Article> {
  return apiRequest<Article>("/api/random");
}

export function getPageInfo(articleId: number): Promise<PageInfo> {
  return apiRequest<PageInfo>(`/api/article/${articleId}/info`);
}

export function getSpecialPages(): Promise<SpecialPage[]> {
  return apiRequest<SpecialPage[]>("/api/special/pages");
}

export function getNamespaces(): Promise<NamespaceInfo[]> {
  return apiRequest<NamespaceInfo[]>("/api/namespaces");
}

export function getTalkMessages(articleId: number): Promise<TalkMessage[]> {
  return apiRequest<TalkMessage[]>(`/api/article/${articleId}/talk`);
}

export function createTalkMessage(articleId: number, body: string, token: string): Promise<TalkMessage> {
  return apiRequest<TalkMessage>(`/api/article/${articleId}/talk`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ body })
  });
}


export type CategoryMember = {
  id: number;
  title: string;
};

export function getCategoryMembers(categoryName: string): Promise<CategoryMember[]> {
  return apiRequest<CategoryMember[]>(`/api/category/${categoryName}/members`);
}

export function getWatchlist(token: string): Promise<WatchlistItem[]> {
  return apiRequest<WatchlistItem[]>("/api/watchlist", {
    headers: authHeaders(token)
  });
}

export function addToWatchlist(articleId: number, token: string): Promise<WatchlistItem> {
  return apiRequest<WatchlistItem>(`/api/watchlist/${articleId}`, {
    method: "POST",
    headers: authHeaders(token)
  });
}

export function removeFromWatchlist(articleId: number, token: string): Promise<void> {
  return apiRequest<void>(`/api/watchlist/${articleId}`, {
    method: "DELETE",
    headers: authHeaders(token)
  });
}


export function getPageProtection(articleId: number): Promise<PageProtection | null> {
  return apiRequest<PageProtection | null>(`/api/article/${articleId}/protection`).catch((e) => {
    if (e.message.includes("404")) return null;
    throw e;
  });
}

export function updateProtection(articleId: number, level: string, reason: string, token: string): Promise<PageProtection> {
  return apiRequest<PageProtection>(`/api/article/${articleId}/protection`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify({ level, reason })
  });
}

export function deleteProtection(articleId: number, token: string): Promise<void> {
  return apiRequest<void>(`/api/article/${articleId}/protection`, {
    method: "DELETE",
    headers: authHeaders(token)
  });
}


export function getBacklinks(articleId: number): Promise<Backlink[]> {
  return apiRequest<Backlink[]>(`/api/article/${articleId}/backlinks`);
}

export function getRedirects(): Promise<RedirectItem[]> {
  return apiRequest<RedirectItem[]>("/api/redirects");
}

export function getFiles(): Promise<FileAsset[]> {
  return apiRequest<FileAsset[]>("/api/files");
}

export async function uploadFile(file: File, title: string, description: string, token: string): Promise<FileAsset> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);
  formData.append("description", description);

  const response = await fetch(`${API_URL}/api/files/upload`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      // ignore
    }
    throw new Error(message || "Upload failed");
  }

  return response.json() as Promise<FileAsset>;
}

export function getTemplates(): Promise<TemplateItem[]> {
  return apiRequest<TemplateItem[]>("/api/templates");
}

export function createTemplate(name: string, content: string, description: string, token: string): Promise<TemplateItem> {
  return apiRequest<TemplateItem>("/api/templates", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ name, content, description })
  });
}

export function getPatrolQueue(): Promise<PatrolItem[]> {
  return apiRequest<PatrolItem[]>("/api/patrol");
}

export function getStatistics(): Promise<Statistics> {
  return apiRequest<Statistics>("/api/statistics");
}
