import NextAuth from "next-auth"
import Credentials from "next-auth/providers/credentials"
import { getBackendUrl, getNextAuthSecret } from "@/lib/settings"

export const { handlers, signIn, signOut, auth } = NextAuth({
  secret: getNextAuthSecret(),
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null
        try {
          const res = await fetch(
            `${getBackendUrl()}/api/v1/admin/internal/auth/verify`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "x-service-token": getNextAuthSecret(),
              },
              body: JSON.stringify({
                email: credentials.email,
                password: credentials.password,
              }),
            }
          )
          if (!res.ok) return null
          const user = await res.json()
          if (!user?.id || !user?.email || !user?.role) return null
          return { id: String(user.id), email: user.email, name: user.name ?? null, role: user.role }
        } catch (error) {
          console.error("Auth verification failed:", error)
          return null
        }
      },
    }),
  ],
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user
      const { pathname } = nextUrl

      if (pathname === "/dashboard/login") {
        if (isLoggedIn) return Response.redirect(new URL("/dashboard", nextUrl))
        return true
      }

      if (!isLoggedIn) return false

      if (pathname.startsWith("/dashboard/users") && auth?.user?.role !== "admin") {
        return Response.redirect(new URL("/dashboard", nextUrl))
      }

      return true
    },
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
        token.role = user.role
        token.checkedAt = Date.now()
        return token
      }

      // Re-check role and active status every 5 minutes
      if (Date.now() - token.checkedAt < 5 * 60 * 1000) return token

      try {
        const res = await fetch(
          `${getBackendUrl()}/api/v1/admin/internal/user-check`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "x-service-token": getNextAuthSecret(),
            },
            body: JSON.stringify({ user_id: Number(token.id) }),
          }
        )
        if (!res.ok) return null
        const { role, active } = await res.json()
        if (!active) return null
        token.role = role
        token.checkedAt = Date.now()
      } catch {
        return null
      }

      return token
    },
    session({ session, token }) {
      session.user.id = token.id
      session.user.role = token.role
      return session
    },
  },
  pages: {
    signIn: "/dashboard/login",
  },
  session: { strategy: "jwt", maxAge: 8 * 60 * 60 },
  trustHost: true,
})
