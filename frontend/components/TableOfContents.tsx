"use client";

import { useMemo } from "react";

import { stripHtml } from "@/lib/format";

type Heading = {
  id: string;
  level: number;
  text: string;
};

type TableOfContentsProps = {
  html: string;
};

export default function TableOfContents({ html }: TableOfContentsProps) {
  const headings = useMemo(() => {
    const matches = Array.from(html.matchAll(/<h([2-6]) id="([^"]+)">([\s\S]*?)<\/h\1>/g));
    return matches.map<Heading>((match) => ({
      level: Number(match[1]),
      id: match[2],
      text: stripHtml(match[3])
    }));
  }, [html]);

  if (headings.length === 0) {
    return null;
  }

  return (
    <aside className="toc" aria-label="Table of contents">
      <h2>Contents</h2>
      <ol>
        {headings.map((heading) => (
          <li key={heading.id} style={{ paddingInlineStart: `${Math.max(heading.level - 2, 0) * 12}px` }}>
            <a href={`#${heading.id}`}>{heading.text}</a>
          </li>
        ))}
      </ol>
    </aside>
  );
}

