import type { UserRole } from "@/client"

export const USER_ROLES = ["ADMIN", "FREELANCER"] as const satisfies [UserRole, ...UserRole[]]

export const ROLE_LABELS: Record<UserRole, string> = {
  ADMIN: "Admin",
  FREELANCER: "Freelancer",
}

export const DEFAULT_ROLE: UserRole = "FREELANCER"
