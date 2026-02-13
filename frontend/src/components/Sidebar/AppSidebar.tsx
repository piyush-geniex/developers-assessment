import { BarChart3, CreditCard, Home, ListTodo, Timer, Users } from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

const commonItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  // { icon: Briefcase, title: "Items", path: "/items" },
  { icon: BarChart3, title: "Worklogs", path: "/worklogs" },
]

const freelancerItems: Item[] = [
  { icon: ListTodo, title: "Tasks", path: "/tasks" },
  { icon: Timer, title: "Time Entries", path: "/time-entries" },
]

const adminItems: Item[] = [
  { icon: CreditCard, title: "Payments", path: "/payments" },
  { icon: Users, title: "Admin", path: "/admin" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const isAdmin = currentUser?.is_superuser || currentUser?.role === "ADMIN"

  const items = isAdmin
    ? [...commonItems, ...adminItems]
    : [...commonItems, ...freelancerItems]

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
