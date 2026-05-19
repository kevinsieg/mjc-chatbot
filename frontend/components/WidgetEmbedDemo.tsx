"use client";

import Script from "next/script";
import Link from "next/link";
import { getWidgetEmbedSnippet, getWidgetScriptUrl } from "@/lib/widgetBaseUrl";
import styles from "./WidgetEmbedDemo.module.css";

/** Simulates an external site that loads the chatbot via widget.js. */
export function WidgetEmbedDemo() {
  const scriptUrl = getWidgetScriptUrl();

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>Test widget — intégration embed</h1>
      <p className={styles.lead}>
        Cette vue simule un site externe (ex. mjcfecamp.org) qui n&apos;inclut que le
        script ci-dessous. Le panneau charge <code>/embed</code> dans une iframe.
      </p>
      <pre className={styles.snippet}>{getWidgetEmbedSnippet()}</pre>
      <p className={styles.hint}>
        URL du script : <code>{scriptUrl}</code> (via{" "}
        <code>NEXT_PUBLIC_WIDGET_BASE_URL</code>)
      </p>
      <ul className={styles.checklist}>
        <li>Bulle Goëllan en bas à droite</li>
        <li>Clic → iframe vers <code>/embed</code></li>
        <li>Re-clic → panneau masqué, conversation conservée</li>
      </ul>
      <p className={styles.links}>
        <Link href="/">← Interface chatbot complète</Link>
        {" · "}
        <a href="/embed" target="_blank" rel="noreferrer">
          Ouvrir /embed seul
        </a>
        {" · "}
        <Link href="/widget-test">Page de test widget</Link>
      </p>
      <Script src={scriptUrl} strategy="afterInteractive" />
    </main>
  );
}
