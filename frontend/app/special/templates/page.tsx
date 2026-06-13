import Link from "next/link";
import { Braces, Plus } from "lucide-react";

import { getTemplates } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function TemplatesPage() {
  const templates = await getTemplates().catch(() => []);

  return (
    <main className="content-page narrow">
      <header className="section-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Braces size={28} />
          <div>
            <h1>Templates</h1>
            <p>Reusable wiki snippets.</p>
          </div>
        </div>
        <Link href="/special/templates/new" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', textDecoration: 'none' }}>
          <Plus size={16} /> New Template
        </Link>
      </header>
      <section className="result-list">
        {templates.map((template) => (
          <article className="result-item" key={template.id}>
            <h3>Template:{template.name}</h3>
            <p>{template.description}</p>
            <pre className="code-sample">{template.content}</pre>
            <span>Updated {formatDate(template.updated_at)}</span>
          </article>
        ))}
        {templates.length === 0 ? <p className="notice">No templates are available.</p> : null}
      </section>
    </main>
  );
}

