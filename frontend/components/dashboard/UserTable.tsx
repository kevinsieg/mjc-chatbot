"use client"

import { useState } from "react"
import type { User } from "@/lib/types"
import styles from "./UserTable.module.css"

interface Props {
  users: User[]
  isAdmin: boolean
}

export default function UserTable({ users: initial, isAdmin }: Props) {
  const [users, setUsers] = useState(initial)
  const [error, setError] = useState("")
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingName, setEditingName] = useState("")
  const [editingEmailId, setEditingEmailId] = useState<number | null>(null)
  const [editingEmail, setEditingEmail] = useState("")
  const [editingPasswordId, setEditingPasswordId] = useState<number | null>(null)
  const [editingPassword, setEditingPassword] = useState("")

  async function handleRoleChange(id: number, role: string) {
    const res = await fetch(`/api/admin/users/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    })
    if (!res.ok) {
      setError("Erreur lors du changement de rôle.")
      return
    }
    const updated = await res.json()
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, role: updated.role } : u)))
    setError("")
  }

  async function handleNameSave(id: number) {
    const name = editingName.trim() || null
    const res = await fetch(`/api/admin/users/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    })
    if (!res.ok) {
      setError("Erreur lors de la modification du nom.")
      setEditingId(null)
      return
    }
    const updated = await res.json()
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, name: updated.name } : u)))
    setEditingId(null)
    setError("")
  }

  async function handleEmailSave(id: number) {
    const email = editingEmail.trim()
    if (!email) { setEditingEmailId(null); return }
    const res = await fetch(`/api/admin/users/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(res.status === 409 ? "Cet email est déjà utilisé." : (body.detail ?? "Erreur lors de la modification de l'email."))
      setEditingEmailId(null)
      return
    }
    const updated = await res.json()
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, email: updated.email } : u)))
    setEditingEmailId(null)
    setError("")
  }

  async function handlePasswordSave(id: number) {
    const password = editingPassword
    if (!password) { setEditingPasswordId(null); return }
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.")
      setEditingPasswordId(null)
      setEditingPassword("")
      return
    }
    const res = await fetch(`/api/admin/users/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    })
    setEditingPasswordId(null)
    setEditingPassword("")
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail ?? "Erreur lors du changement de mot de passe.")
      return
    }
    setError("")
  }

  async function handleDelete(id: number) {
    if (!confirm("Désactiver cet utilisateur ?")) return
    const res = await fetch(`/api/admin/users/${id}`, { method: "DELETE" })
    if (!res.ok) {
      setError("Erreur lors de la désactivation.")
      return
    }
    setUsers((prev) => prev.map((u) => u.id === id ? { ...u, deleted_at: new Date().toISOString() } : u))
    setError("")
  }

  return (
    <>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Email</th>
            <th>Nom</th>
            <th>Rôle</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id} className={user.deleted_at ? styles.deleted : undefined}>
              <td
                className={isAdmin && !user.deleted_at ? styles.nameCell : undefined}
                onClick={() => {
                  if (isAdmin && !user.deleted_at) {
                    setEditingEmailId(user.id)
                    setEditingEmail(user.email)
                  }
                }}
              >
                {editingEmailId === user.id ? (
                  <input
                    autoFocus
                    type="email"
                    className={styles.nameInput}
                    value={editingEmail}
                    onChange={(e) => setEditingEmail(e.target.value)}
                    onBlur={() => handleEmailSave(user.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleEmailSave(user.id)
                      if (e.key === "Escape") setEditingEmailId(null)
                    }}
                  />
                ) : (
                  user.email
                )}
              </td>
              <td
                className={isAdmin && !user.deleted_at ? styles.nameCell : undefined}
                onClick={() => {
                  if (isAdmin && !user.deleted_at) {
                    setEditingId(user.id)
                    setEditingName(user.name ?? "")
                  }
                }}
              >
                {editingId === user.id ? (
                  <input
                    autoFocus
                    className={styles.nameInput}
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onBlur={() => handleNameSave(user.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleNameSave(user.id)
                      if (e.key === "Escape") setEditingId(null)
                    }}
                  />
                ) : (
                  user.name ?? "—"
                )}
              </td>
              <td>
                <select
                  value={user.role}
                  onChange={(e) => handleRoleChange(user.id, e.target.value)}
                  className={styles.select}
                  disabled={!!user.deleted_at}
                >
                  <option value="staff">staff</option>
                  <option value="admin">admin</option>
                </select>
              </td>
              <td className={styles.actions}>
                {isAdmin && !user.deleted_at && (
                  editingPasswordId === user.id ? (
                    <input
                      autoFocus
                      type="password"
                      placeholder="Nouveau mot de passe"
                      className={styles.nameInput}
                      value={editingPassword}
                      onChange={(e) => setEditingPassword(e.target.value)}
                      onBlur={() => handlePasswordSave(user.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handlePasswordSave(user.id)
                        if (e.key === "Escape") { setEditingPasswordId(null); setEditingPassword("") }
                      }}
                    />
                  ) : (
                    <button
                      onClick={() => { setEditingPasswordId(user.id); setEditingPassword("") }}
                      className={styles.actionBtn}
                    >
                      Mot de passe
                    </button>
                  )
                )}
                <button
                  onClick={() => handleDelete(user.id)}
                  disabled={!!user.deleted_at}
                  className={styles.deleteBtn}
                >
                  Désactiver
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {error && <p className={styles.error}>{error}</p>}
    </>
  )
}
