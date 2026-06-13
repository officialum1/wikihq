import { Boxes } from "lucide-react";

import { getNamespaces } from "@/lib/api";

export default async function NamespacesPage() {
  const namespaces = await getNamespaces().catch(() => []);

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <Boxes size={28} />
        <div>
          <h1>Namespaces</h1>
          <p>Configured wiki namespaces.</p>
        </div>
      </header>
      <section className="result-list">
        {namespaces.map((namespace) => (
          <article className="result-item" key={namespace.id}>
            <h3>{namespace.name}</h3>
            <p>{namespace.description}</p>
            <span>{namespace.slug}</span>
          </article>
        ))}
      </section>
    </main>
  );
}

