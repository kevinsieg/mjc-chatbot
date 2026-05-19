import Script from "next/script";
import Link from "next/link";
import {
  getWidgetBaseUrl,
  getWidgetEmbedSnippet,
  getWidgetScriptUrl,
  isWidgetBaseUrlConfigured,
} from "@/lib/widgetBaseUrl";
import styles from "./page.module.css";

/** Simulates an external site loading the chatbot via widget.js. */
export default function WidgetTestPage() {
  if (!isWidgetBaseUrlConfigured()) {
    return (
      <main className={styles.main}>
        <h1 className={styles.title}>Configuration manquante</h1>
        <p>
          Définissez <code>NEXT_PUBLIC_WIDGET_BASE_URL</code> puis reconstruisez le
          frontend (<code>make dev-build</code>).
        </p>
        <p>
          Ex. local : <code>http://localhost:3000</code> — VPS :{" "}
          <code>http://162.19.241.44:3000</code>
        </p>
      </main>
    );
  }

  const scriptUrl = getWidgetScriptUrl();
  const configuredBase = getWidgetBaseUrl();

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>Page de test — Widget MJC</h1>
      <p>Cette page simule un site externe qui embarque le chatbot MJC.</p>
      <p>
        Le bouton <strong>Goëllan</strong> doit apparaître en bas à droite.
      </p>
      <ul className={styles.list}>
        <li>Cliquer sur la bulle → le panneau chat s&apos;ouvre</li>
        <li>Cliquer à nouveau → le panneau se cache (conversation conservée)</li>
        <li>
          Cliquer une troisième fois → le panneau réapparaît avec la conversation
        </li>
      </ul>
      <p>
        Base (<code>NEXT_PUBLIC_WIDGET_BASE_URL</code>) :{" "}
        <code>{configuredBase}</code>
      </p>
      <p>
        Widget chargé depuis : <code>{scriptUrl}</code>
      </p>
      <pre className={styles.snippet}>{getWidgetEmbedSnippet()}</pre>
      <p className={styles.links}>
        <Link href="/">← Interface chatbot</Link>
        {" · "}
        <a href="/embed" target="_blank" rel="noreferrer">
          Ouvrir /embed seul
        </a>
      </p>
      <Script src={scriptUrl} strategy="afterInteractive" />
    </main>
  );
}
