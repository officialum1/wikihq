"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileUp } from "lucide-react";
import { uploadFile, getStoredToken } from "@/lib/api";

export default function FileUploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const token = getStoredToken();
    if (!token) {
      setError("You must be logged in to upload a file.");
      setLoading(false);
      return;
    }

    if (!file) {
      setError("Please select a file to upload.");
      setLoading(false);
      return;
    }

    try {
      await uploadFile(file, title || file.name, description, token);
      router.push("/special/files");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to upload file.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="content-page narrow">
      <header className="section-heading">
        <FileUp size={28} />
        <div>
          <h1>Upload File</h1>
          <p>Upload a new image or media asset.</p>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="edit-form">
        <div className="form-group">
          <label htmlFor="file">Select File</label>
          <input
            id="file"
            type="file"
            onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                    setFile(e.target.files[0]);
                    if (!title) setTitle(e.target.files[0].name);
                }
            }}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="title">Destination Title (Optional)</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., File:MyImage.jpg"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Summary / Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={5}
            placeholder="What is this file? Provide a source or license."
          />
        </div>

        <div className="form-actions">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Uploading..." : "Upload File"}
          </button>
        </div>
      </form>
    </main>
  );
}
