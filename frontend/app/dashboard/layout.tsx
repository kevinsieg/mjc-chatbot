import Image from "next/image"
import { auth, signOut } from "@/auth"
import styles from "./layout.module.css"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()

  return (
    <div className={styles.shell}>
      {session && (
        <nav className={styles.nav}>
          <a href="/dashboard" className={styles.brand}>
            <div className={styles.logoWrap}>
              <Image src="/brand/mjc_logo.jpg" alt="MJC Fécamp" width={36} height={36} className={styles.logo} />
            </div>
            <span className={styles.brandName}>MJC Dashboard</span>
          </a>
          <div className={styles.navLinks}>
            <a href="/" className={styles.link}>Chatbot</a>
            <a href="/dashboard" className={styles.link}>Statistiques</a>
            {session.user.role === "admin" && (
              <a href="/dashboard/users" className={styles.link}>Utilisateurs</a>
            )}
            {session.user.role === "admin" && (
              <a href="/widget-test" className={styles.link}>Widget</a>
            )}
          </div>
          <form
            action={async () => {
              "use server"
              await signOut({ redirectTo: "/dashboard/login" })
            }}
          >
            <button type="submit" className={styles.signout}>
              {session.user.email} — Déconnexion
            </button>
          </form>
        </nav>
      )}
      <main className={styles.content}>{children}</main>
    </div>
  )
}
