import { auth } from "@/auth"
import { adminFetch } from "@/lib/admin-api"
import type { User } from "@/lib/types"
import UserTable from "@/components/dashboard/UserTable"
import AddUserSection from "./AddUserSection"
import styles from "./users.module.css"

interface PagedUsers {
  items: User[]
  total: number
}

export default async function UsersPage() {
  const [session, { items, total }] = await Promise.all([
    auth(),
    adminFetch<PagedUsers>("/users"),
  ])

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.heading}>Utilisateurs ({total})</h1>
        <AddUserSection />
      </div>
      <div className={styles.tableWrap}>
        <UserTable users={items} isAdmin={session?.user?.role === "admin"} />
      </div>
    </div>
  )
}
