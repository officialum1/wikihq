import { MetadataRoute } from "next";

type SitemapArticle = {
  title: string;
  updated_at: string;
};

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://wikihq.org";
  
  const sitemapUrls: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}/`,
      lastModified: new Date(),
      changeFrequency: "hourly",
      priority: 1,
    },
    {
      url: `${baseUrl}/search`,
      lastModified: new Date(),
      changeFrequency: "hourly",
      priority: 0.8,
    },
  ];

  try {
    const apiBase = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${apiBase}/api/sitemap`, { next: { revalidate: 3600 } });
    if (res.ok) {
      const articles: SitemapArticle[] = await res.json();
      articles.forEach((article) => {
        const encodedTitle = encodeURIComponent(article.title.replace(/ /g, "_"));
        sitemapUrls.push({
          url: `${baseUrl}/wiki/${encodedTitle}`,
          lastModified: new Date(article.updated_at),
          changeFrequency: "weekly",
          priority: 0.6,
        });
      });
    }
  } catch (error) {
    console.error("Failed to fetch sitemap data from API", error);
  }

  return sitemapUrls;
}
