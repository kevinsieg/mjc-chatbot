"use client";

import { useCallback, useEffect, useState } from "react";
import { Chat } from "@/components/Chat";
import { RagKnowledgeViewer } from "@/components/RagKnowledgeViewer";
import { SystemPromptEditor } from "@/components/SystemPromptEditor";

const SESSION_STORAGE_KEY = "mjc-system-prompt-override";

/** Home page chat with editable system prompt (session-only override). */
export function HomeChatPanel() {
  const [defaultPrompt, setDefaultPrompt] = useState("");
  const [promptValue, setPromptValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/backend/api/v1/system-prompt");
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        const data = (await res.json()) as { default?: string };
        if (typeof data.default !== "string" || !data.default.trim()) {
          throw new Error("Invalid response: missing default system prompt");
        }
        if (cancelled) return;
        const stored = sessionStorage.getItem(SESSION_STORAGE_KEY);
        setDefaultPrompt(data.default);
        setPromptValue(stored ?? data.default);
      } catch (e: unknown) {
        if (cancelled) return;
        const message = e instanceof Error ? e.message : String(e);
        setLoadError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const persistPrompt = useCallback(
    (value: string) => {
      setPromptValue(value);
      if (!defaultPrompt) return;
      if (value === defaultPrompt) {
        sessionStorage.removeItem(SESSION_STORAGE_KEY);
      } else {
        sessionStorage.setItem(SESSION_STORAGE_KEY, value);
      }
    },
    [defaultPrompt],
  );

  const handleReset = useCallback(() => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    setPromptValue(defaultPrompt);
  }, [defaultPrompt]);

  const systemPromptOverride =
    !loading && defaultPrompt && promptValue !== defaultPrompt ? promptValue : undefined;

  return (
    <>
      <Chat systemPromptOverride={systemPromptOverride} />
      <SystemPromptEditor
        value={promptValue}
        defaultPrompt={defaultPrompt}
        loading={loading}
        loadError={loadError}
        onChange={persistPrompt}
        onReset={handleReset}
      />
      <RagKnowledgeViewer />
    </>
  );
}
