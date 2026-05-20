"use client"

import { useState, useEffect } from "react"
import styles from "./PrivacyBanner.module.css"

const CONSENT_KEY = "mjc-privacy-consent"

export default function PrivacyBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem(CONSENT_KEY)) {
      setVisible(true)
    }
  }, [])

  function dismiss() {
    localStorage.setItem(CONSENT_KEY, "1")
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className={styles.banner}>
      <p className={styles.text}>
        Ce chatbot enregistre les échanges de manière anonyme (session UUID, pas de contenu) à des fins statistiques.
        Aucune donnée personnelle n&apos;est conservée.
      </p>
      <button onClick={dismiss} className={styles.btn}>Compris</button>
    </div>
  )
}
