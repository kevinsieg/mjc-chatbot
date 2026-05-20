import Image from "next/image";
import { HomeChatPanel } from "@/components/HomeChatPanel";
import { HealthBadge } from "@/components/HealthBadge";
import { brand } from "@/brand/brand";
import styles from "./page.module.css";
import PrivacyBanner from "@/components/PrivacyBanner";

export default function Home() {
  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <Image
          className={styles.logo}
          src={brand.assets.mjcLogo}
          alt={`${brand.name} — logo`}
          width={44}
          height={44}
          priority
        />
        <h1 className={styles.title}>{brand.productName}</h1>
        <HealthBadge />
        <a href="/dashboard" className={styles.dashboardLink}>Dashboard</a>
      </header>

      <HomeChatPanel />

      <footer className={styles.footer}>
        <p>
          Développé par le Club IA de Fécamp —{" "}
          <a href="http://mjcfecamp.org" target="_blank" rel="noreferrer">
            mjcfecamp.org
          </a>{" "}
          ·{" "}
          <a href="https://www.club-ia-plus.fr" target="_blank" rel="noreferrer">
            club-ia-plus.fr
          </a>
        </p>
      </footer>
      <PrivacyBanner />
    </main>
  );
}
