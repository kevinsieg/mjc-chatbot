"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Chat } from "@/components/Chat";
import { brand } from "@/brand/brand";
import styles from "./page.module.css";

export default function EmbedPage() {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    fetch("/api/backend/health", { signal: controller.signal })
      .then((r) => setHealthy(r.ok))
      .catch(() => setHealthy(false))
      .finally(() => clearTimeout(timeoutId));

    return () => {
      controller.abort();
      clearTimeout(timeoutId);
    };
  }, []);

  if (!healthy && healthy !== null) {
    return (
      <div className={styles.error}>
        <Image
          src={brand.assets.mascot}
          alt="Goëllan"
          width={64}
          height={72}
        />
        <p>
          Service temporairement indisponible.
          <br />
          Veuillez réessayer plus tard.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      {healthy && <Chat />}
    </div>
  );
}
