import { NextRequest, NextResponse } from "next/server"
import { auth } from "@/auth"
import { adminFetch } from "@/lib/admin-api"

type Params = { params: Promise<{ id: string }> }

export async function PATCH(req: NextRequest, { params }: Params) {
  const session = await auth()
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 })
  if (session.user.role !== "admin") return NextResponse.json({ detail: "Forbidden" }, { status: 403 })

  try {
    const { id } = await params
    const body = await req.json()
    const user = await adminFetch(`/users/${id}`, { method: "PATCH", body: JSON.stringify(body) })
    return NextResponse.json(user)
  } catch (err) {
    const e = err as { status?: number; detail?: string }
    return NextResponse.json({ detail: e.detail ?? "Request failed" }, { status: e.status ?? 500 })
  }
}

export async function DELETE(_req: NextRequest, { params }: Params) {
  const session = await auth()
  if (!session) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 })
  if (session.user.role !== "admin") return NextResponse.json({ detail: "Forbidden" }, { status: 403 })

  try {
    const { id } = await params
    await adminFetch(`/users/${id}`, { method: "DELETE" })
    return new NextResponse(null, { status: 204 })
  } catch (err) {
    const e = err as { status?: number; detail?: string }
    return NextResponse.json({ detail: e.detail ?? "Request failed" }, { status: e.status ?? 500 })
  }
}
