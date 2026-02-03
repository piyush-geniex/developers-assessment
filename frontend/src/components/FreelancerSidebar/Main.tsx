import { Link, useRouterState } from "@tanstack/react-router"
import type { LucideIcon } from "lucide-react"

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface MenuItem {
  icon: LucideIcon
  title: string
  path: string
}

interface FreelancerMainProps {
  items: MenuItem[]
}

function FreelancerMain({ items }: FreelancerMainProps) {
  const { isMobile, setOpenMobile } = useSidebar()
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  const handleClick = () => {
    if (isMobile) {
      setOpenMobile(false)
    }
  }

  return (
    <SidebarGroup>
      <SidebarMenu>
        <TooltipProvider delayDuration={0}>
          {items.map((item) => {
            // Check for exact match or if current path starts with item path (for nested routes)
            const isActive =
              currentPath === item.path ||
              (item.path !== "/freelancer" &&
                currentPath.startsWith(item.path))

            return (
              <SidebarMenuItem key={item.title}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <SidebarMenuButton asChild isActive={isActive}>
                      <Link to={item.path as any} onClick={handleClick}>
                        <item.icon />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </TooltipTrigger>
                  <TooltipContent side="right">{item.title}</TooltipContent>
                </Tooltip>
              </SidebarMenuItem>
            )
          })}
        </TooltipProvider>
      </SidebarMenu>
    </SidebarGroup>
  )
}

export default FreelancerMain
