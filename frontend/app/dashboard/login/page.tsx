"use client"

import { signIn } from "next-auth/react"
import { useState, FormEvent } from "react"
import Image from "next/image"
import styles from "./login.module.css"

export default function LoginPage() {
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setLoading(true)
    const data = new FormData(e.currentTarget)
    const result = await signIn("credentials", {
      email: data.get("email"),
      password: data.get("password"),
      redirect: false,
    })
    setLoading(false)
    if (result?.error) {
      setError("Identifiants invalides.")
    } else {
      window.location.href = "/dashboard"
    }
  }

  return (
    <main className={styles.container}>
      <div className={styles.card}>
        <Image
          src="/brand/goellan.png"
          alt="Goëllan"
          width={100}
          height={100}
          className={styles.mascot}
          priority
        />
        <h1 className={styles.title}>Tableau de bord</h1>
        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Email
            <input
              name="email"
              type="email"
              required
              autoComplete="email"
              className={styles.input}
            />
          </label>
          <label className={styles.label}>
            Mot de passe
            <div className={styles.passwordWrapper}>
              <input
                name="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                className={styles.input}
              />
              <button
                type="button"
                className={styles.eyeButton}
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
              >
                {showPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                )}
              </button>
            </div>
          </label>
          {error && <p className={styles.error}>{error}</p>}
          <button type="submit" disabled={loading} className={styles.button}>
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
        <div className={styles.logoRow}>
          <Image
            src="/brand/mjc_logo.jpg"
            alt="MJC Fécamp"
            width={56}
            height={56}
            className={styles.logo}
            priority
          />
        </div>
        </div>
    </main>
  )
}
