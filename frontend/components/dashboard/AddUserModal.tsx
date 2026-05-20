"use client"

import { useState, FormEvent } from "react"
import type { User } from "@/lib/types"
import styles from "./AddUserModal.module.css"

interface Props {
  onAdded: (user: User) => void
  onClose: () => void
}

export default function AddUserModal({ onAdded, onClose }: Props) {
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setLoading(true)
    const data = new FormData(e.currentTarget)
    const res = await fetch("/api/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: data.get("email"),
        name: data.get("name") || null,
        password: data.get("password"),
        role: data.get("role"),
      }),
    })
    setLoading(false)
    if (!res.ok) {
      if (res.status === 409) {
        setError("Cet email est déjà utilisé par un autre utilisateur.")
      } else {
        const body = await res.json().catch(() => ({}))
        setError(body.detail ?? "Erreur lors de la création.")
      }
      return
    }
    const user = await res.json()
    onAdded(user)
    onClose()
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Ajouter un utilisateur</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Email
            <input name="email" type="email" required className={styles.input} />
          </label>
          <label className={styles.label}>
            Nom (optionnel)
            <input name="name" type="text" className={styles.input} />
          </label>
          <label className={styles.label}>
            Mot de passe
            <input name="password" type="password" required minLength={8} className={styles.input} />
          </label>
          <label className={styles.label}>
            Rôle
            <select name="role" className={styles.input}>
              <option value="staff">staff</option>
              <option value="admin">admin</option>
            </select>
          </label>
          {error && <p className={styles.error}>{error}</p>}
          <div className={styles.actions}>
            <button type="button" onClick={onClose} className={styles.cancel}>Annuler</button>
            <button type="submit" disabled={loading} className={styles.submit}>
              {loading ? "Création…" : "Créer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
