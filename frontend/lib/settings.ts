export function getBackendUrl(): string {
  return process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000"
}

export function getNextAuthSecret(): string {
  const secret = process.env.NEXTAUTH_SECRET ?? ""
  if (!secret) throw new Error("NEXTAUTH_SECRET is not set")
  return secret
}
