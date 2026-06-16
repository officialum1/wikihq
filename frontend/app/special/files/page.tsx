import Link from "next/link";
import { FileImage, Upload } from "lucide-react";

import { getFiles } from "@/lib/api";
import { formatDate } from "@/lib/format";

export default async function FilesPage() {
  const files = await getFiles().catch(() => []);

  return (
    <main className="content-page narrow">
      <header className="section-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <FileImage size={28} />
          <div>
            <h1>Files</h1>
            <p>Media description records.</p>
          </div>
        </div>
        <Link href="/special/files/upload" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', textDecoration: 'none' }}>
          <Upload size={16} /> Upload File
        </Link>
      </header>
      <section className="result-list">
        {files.map((file) => (
          <article className="result-item" key={file.id}>
            <h3>{file.title}</h3>
            <p>{file.description}</p>
            <span>{file.filename} · {file.mime_type} · {file.size_bytes.toLocaleString()} bytes · {formatDate(file.created_at)}</span>
          </article>
        ))}
        {files.length === 0 ? <p className="notice">No files are available.</p> : null}
      </section>
    </main>
  );
}

