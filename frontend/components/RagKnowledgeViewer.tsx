"use client";

import { useCallback, useState } from "react";
import styles from "./RagKnowledgeViewer.module.css";

type KnowledgeFile = {
  path: string;
  content: string;
};

/** Read-only collapsible viewer for Markdown RAG sources under DATA_DIR. */
export function RagKnowledgeViewer() {
  const [files, setFiles] = useState<KnowledgeFile[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFiles = useCallback(async () => {
    if (files !== null || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/backend/api/v1/knowledge-sources");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = (await res.json()) as { files?: KnowledgeFile[] };
      if (!Array.isArray(data.files)) {
        throw new Error("Invalid response: missing files array");
      }
      for (const file of data.files) {
        if (typeof file.path !== "string" || typeof file.content !== "string") {
          throw new Error("Invalid response: invalid file entry");
        }
      }
      setFiles(data.files);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [files, loading]);

  const handleToggle = useCallback(
    (e: React.SyntheticEvent<HTMLDetailsElement>) => {
      if (e.currentTarget.open) void loadFiles();
    },
    [loadFiles],
  );

  return (
    <details className={styles.wrap} onToggle={handleToggle}>
      <summary className={styles.summary}>Données Markdown RAG (lecture seule)</summary>
      <div className={styles.body}>
        <p className={styles.hint}>
          Fichiers indexés par <code>make dev-data</code> et utilisés pour le contexte «&nbsp;Contextes
          internes&nbsp;». Affichage en lecture seule.
        </p>
        {loading && <p className={styles.loading}>Chargement…</p>}
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        {files?.map((file) => (
          <details key={file.path} className={styles.fileWrap}>
            <summary className={styles.fileSummary}>{file.path}</summary>
            <div className={styles.fileBody}>
              <pre className={styles.content}>{file.content}</pre>
            </div>
          </details>
        ))}
      </div>
    </details>
  );
}
