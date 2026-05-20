import { NextRequest, NextResponse } from "next/server"
import { auth } from "@/auth"
import { adminFetch } from "@/lib/admin-api"

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 })
  if (session.user.role !== "admin") return NextResponse.json({ detail: "Forbidden" }, { status: 403 })

  try {
    const body = await req.json()
    const user = await adminFetch("/users", { method: "POST", body: JSON.stringify(body) })
    return NextResponse.json(user, { status: 201 })
  } catch (err) {
    const e = err as { status?: number; detail?: string }
    return NextResponse.json({ detail: e.detail ?? "Request failed" }, { status: e.status ?? 500 })
  }
}
