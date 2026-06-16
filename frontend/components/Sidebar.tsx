import Link from "next/link";
import { BookOpen, Clock, Dice5, FileText, Gauge, Globe, Link2, ListTree, MessageSquare, Shield, Tags } from "lucide-react";

import { titleToPath } from "@/lib/api";

type SidebarProps = {
  categories?: string[];
  interlanguageLinks?: Record<string, string>;
  title?: string;
};

export default function Sidebar({ categories = [], interlanguageLinks = {}, title }: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Article navigation">
      <nav>
        <Link href="/wiki/Main_Page">
          <BookOpen size={16} />
          Main Page
        </Link>
        <Link href="/search">
          <Clock size={16} />
          Recent Search
        </Link>
        <Link href="/admin/progress">
          <Gauge size={16} />
          Import Progress
        </Link>
        <Link href="/special">
          <ListTree size={16} />
          Special Pages
        </Link>
        <Link href="/special/random">
          <Dice5 size={16} />
          Random Article
        </Link>
      </nav>
      {title ? (
        <section>
          <h2>
            <FileText size={15} />
            Page tools
          </h2>
          <nav>
            <Link href={`/wiki/${titleToPath(title)}/talk`}>
              <MessageSquare size={16} />
              Discussion
            </Link>
            <Link href={`/wiki/${titleToPath(title)}/info`}>Page information</Link>
            <Link href={`/wiki/${titleToPath(title)}/history`}>Revision history</Link>
            <Link href={`/wiki/${titleToPath(title)}/edit`}>Edit source</Link>
            <Link href={`/wiki/${titleToPath(title)}/backlinks`}>
              <Link2 size={16} />
              What links here
            </Link>
            <Link href={`/wiki/${titleToPath(title)}/protect`}>
              <Shield size={16} />
              Protection
            </Link>
          </nav>
        </section>
      ) : null}
      <section>
        <h2>
          <Tags size={15} />
          Categories
        </h2>
        {categories.length ? (
          <ul>
            {categories.map((category) => (
              <li key={category}>{category}</li>
            ))}
          </ul>
        ) : (
          <p>No categories</p>
        )}
      </section>
      {Object.keys(interlanguageLinks).length > 0 && (
        <section>
          <h2>
            <Globe size={15} />
            Languages
          </h2>
          <ul>
            {Object.entries(interlanguageLinks).map(([lang, target]) => (
              <li key={lang}>
                <span className="lang-code">{lang}</span>: {target}
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  );
}
