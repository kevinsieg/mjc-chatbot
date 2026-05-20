import styles from "./StatCard.module.css"

interface Props {
  label: string
  value: string | number
}

export default function StatCard({ label, value }: Props) {
  return (
    <div className={styles.card}>
      <span className={styles.value}>{value}</span>
      <span className={styles.label}>{label}</span>
    </div>
  )
}
