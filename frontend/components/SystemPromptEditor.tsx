"use client";

import styles from "./SystemPromptEditor.module.css";

type SystemPromptEditorProps = {
  value: string;
  defaultPrompt: string;
  loading: boolean;
  loadError: string | null;
  onChange: (value: string) => void;
  onReset: () => void;
};

/** Collapsible textarea to view and edit the chat system prompt on the home page. */
export function SystemPromptEditor({
  value,
  defaultPrompt,
  loading,
  loadError,
  onChange,
  onReset,
}: SystemPromptEditorProps) {
  const isDefault = !loading && value === defaultPrompt;

  return (
    <details className={styles.wrap}>
      <summary className={styles.summary}>Instructions système (avancé)</summary>
      {loadError && (
        <p className={styles.error} role="alert">
          {loadError}
        </p>
      )}
      <div className={styles.body}>
        <p className={styles.hint}>
          Instructions de base envoyées au modèle. Le contexte RAG («&nbsp;Contextes internes&nbsp;»)
          est toujours ajouté côté serveur. Les routes embed/widget utilisent le fichier par défaut.
        </p>
        <label className={styles.srOnly} htmlFor="system-prompt-input">
          Instructions système
        </label>
        <textarea
          id="system-prompt-input"
          className={styles.textarea}
          value={value}
          disabled={loading}
          onChange={(e) => onChange(e.target.value)}
        />
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.reset}
            disabled={loading || isDefault}
            onClick={onReset}
          >
            Réinitialiser par défaut
          </button>
        </div>
      </div>
    </details>
  );
}
