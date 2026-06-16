import { redirect } from "next/navigation";

import { getRandomArticle, titleToPath } from "@/lib/api";

export default async function RandomArticlePage() {
  const article = await getRandomArticle().catch(() => null);
  if (!article) {
    redirect("/special");
  }
  redirect(`/wiki/${titleToPath(article.title)}`);
}

