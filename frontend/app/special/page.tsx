import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import Link from "next/link";
import { ListTree } from "lucide-react";

import { getSpecialPages, type SpecialPage } from "@/lib/api";

export default async function SpecialPagesIndex() {
  const pages = await getSpecialPages().catch(() => []);
  const grouped = pages.reduce<Record<string, SpecialPage[]>>((acc, page) => {
    acc[page.section] = acc[page.section] || [];
    acc[page.section].push(page);
    return acc;
  }, {});

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <ListTree size={28} />
        <div>
          <h1>Special Pages</h1>
          <p>System pages for navigation, maintenance, and wiki tools.</p>
        </div>
      </header>
      <div className="special-groups">
        {Object.entries(grouped).map(([section, sectionPages]) => (
          <section className="special-group" key={section}>
            <h2>{section}</h2>
            <div className="result-list">
              {sectionPages.map((page) => (
                <article className="result-item" key={page.path}>
                  <h3>
                    <Link href={page.path}>{page.title}</Link>
                  </h3>
                  <p>{page.description}</p>
                </article>
              ))}
            </div>
          </section>
        ))}
        {pages.length === 0 ? <p className="notice error">Special pages are unavailable.</p> : null}
      </div>
    </main>
  );
}
