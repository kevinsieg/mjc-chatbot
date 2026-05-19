/** Public origin of the chatbot app (no trailing slash). Set via NEXT_PUBLIC_WIDGET_BASE_URL at build. */
export function getWidgetBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_WIDGET_BASE_URL?.trim();
  if (!fromEnv) return "";
  return fromEnv.replace(/\/$/, "");
}

/** True when NEXT_PUBLIC_WIDGET_BASE_URL was set at build time. */
export function isWidgetBaseUrlConfigured(): boolean {
  return getWidgetBaseUrl().length > 0;
}

/** URL of widget.js for embed snippets and test pages. */
export function getWidgetScriptUrl(): string {
  const base = getWidgetBaseUrl();
  if (!base) {
    throw new Error(
      "NEXT_PUBLIC_WIDGET_BASE_URL is required (e.g. http://localhost:3000 or http://162.19.241.44:3000)",
    );
  }
  return `${base}/widget.js`;
}

/** One-line embed snippet for external sites. */
export function getWidgetEmbedSnippet(): string {
  return `<script src="${getWidgetScriptUrl()}"></script>`;
}
