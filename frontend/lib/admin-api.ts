import { SignJWT } from "jose"
import { auth } from "@/auth"
import { getBackendUrl, getNextAuthSecret } from "@/lib/settings"

async function serviceJWT(userId: string, role: string): Promise<string> {
  const secret = new TextEncoder().encode(getNextAuthSecret())
  return new SignJWT({ sub: userId, role })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("60s")
    .sign(secret)
}

export async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const session = await auth()
  if (!session?.user?.id || !session.user.role) {
    throw new Error("Not authenticated")
  }
  const token = await serviceJWT(session.user.id, session.user.role)
  const res = await fetch(`${getBackendUrl()}/api/v1/admin${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw Object.assign(new Error("Admin API error"), { status: res.status, detail: body.detail ?? null })
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return null as T
  }
  return res.json() as Promise<T>
}
