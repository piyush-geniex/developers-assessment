import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { Footer } from "@/components/Common/Footer"
import FreelancerSidebar from "@/components/FreelancerSidebar/FreelancerSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isFreelancerLoggedIn } from "@/client/freelancerPortalService"

export const Route = (createFileRoute as any)("/_freelancer-layout")({
  component: FreelancerLayout,
  beforeLoad: async () => {
    if (!isFreelancerLoggedIn()) {
      throw redirect({
        to: "/freelancer/login",
      })
    }
  },
})

function FreelancerLayout() {
  return (
    <SidebarProvider>
      <FreelancerSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b px-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
          <span className="text-sm font-medium text-muted-foreground">
            Freelancer Portal
          </span>
        </header>
        <main className="flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}

export default FreelancerLayout
