import Image from "next/image"
import { adminFetch } from "@/lib/admin-api"
import type { StatsOverview, DailyPoint, HeatmapPoint, ApiUsageRow, TopSourceRow } from "@/lib/types"
import StatCard from "@/components/dashboard/StatCard"
import ApiUsagePanel from "@/components/dashboard/ApiUsagePanel"
import DailyTrendChart from "@/components/dashboard/DailyTrendChart"
import ActivityHeatmap from "@/components/dashboard/ActivityHeatmap"
import TopSourcesPanel from "@/components/dashboard/TopSourcesPanel"
import styles from "./page.module.css"

export default async function DashboardPage() {
  const [overview, daily, heatmap, apiUsage, topSources] = await Promise.all([
    adminFetch<StatsOverview>("/stats/overview"),
    adminFetch<DailyPoint[]>("/stats/daily"),
    adminFetch<HeatmapPoint[]>("/stats/heatmap"),
    adminFetch<ApiUsageRow[]>("/stats/api-usage"),
    adminFetch<TopSourceRow[]>("/stats/top-sources"),
  ])

  return (
    <div>
      <div className={styles.welcome}>
        <Image src="/brand/goellan.png" alt="Goëllan" width={100} height={100} className={styles.mascot} priority />
        <div className={styles.welcomeText}>
          <h1 className={styles.heading}>Tableau de bord</h1>
          <p className={styles.sub}>Bienvenue sur l'interface d'administration MJC Fécamp.</p>
        </div>
      </div>

      <h2 className={styles.sectionTitle}>Vue d'ensemble</h2>
      <div className={styles.cards}>
        <StatCard label="Sessions totales" value={overview.total_sessions} />
        <StatCard label="Messages totaux" value={overview.total_messages} />
        <StatCard label="Msgs / session" value={overview.avg_messages_per_session.toFixed(1)} />
        <StatCard label="Latence moy." value={`${overview.avg_latency_ms.toFixed(0)} ms`} />
      </div>

      <h2 className={styles.sectionTitle}>Tendances</h2>
      <div className={styles.charts}>
        <DailyTrendChart data={daily} panelClass={styles.panel} titleClass={styles.panelTitle} />
        <TopSourcesPanel data={topSources} panelClass={styles.panel} titleClass={styles.panelTitle} emptyClass={styles.empty} tableClass={styles.table} />
        <ActivityHeatmap data={heatmap} panelClass={`${styles.panel} ${styles.widePanel}`} titleClass={styles.panelTitle} />
        <ApiUsagePanel data={apiUsage} panelClass={`${styles.panel} ${styles.widePanel}`} titleClass={styles.panelTitle} emptyClass={styles.empty} tableClass={styles.table} />
      </div>
    </div>
  )
}
