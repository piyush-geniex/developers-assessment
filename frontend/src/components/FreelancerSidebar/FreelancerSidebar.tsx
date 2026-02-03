import { ClipboardList, CreditCard, Home, User } from "lucide-react"

import { Logo } from "@/components/Common/Logo"
import { SidebarAppearance } from "@/components/Common/Appearance"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"

import FreelancerMain from "./Main"
import FreelancerUser from "./User"

const menuItems = [
  { icon: Home, title: "Dashboard", path: "/freelancer" },
  { icon: ClipboardList, title: "My WorkLogs", path: "/freelancer/worklogs" },
  { icon: CreditCard, title: "Payments", path: "/freelancer/payments" },
  { icon: User, title: "Profile", path: "/freelancer/profile" },
]

function FreelancerSidebar() {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <Logo />
      </SidebarHeader>
      <SidebarContent>
        <FreelancerMain items={menuItems} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <FreelancerUser />
      </SidebarFooter>
    </Sidebar>
  )
}

export default FreelancerSidebar
