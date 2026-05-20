"use client"

import { useState } from "react"
import AddUserModal from "@/components/dashboard/AddUserModal"
import styles from "./users.module.css"

export default function AddUserSection() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button onClick={() => setOpen(true)} className={styles.addBtn}>
        + Ajouter
      </button>
      {open && (
        <AddUserModal
          onAdded={() => { window.location.reload() }}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  )
}
