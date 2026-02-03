import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import {
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  XCircle,
  AlertCircle,
} from "lucide-react"
import { Suspense } from "react"

import { FreelancerPortalService } from "@/client/freelancerPortalService"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useFreelancerAuth from "@/hooks/useFreelancerAuth"

export const Route = (createFileRoute as any)("/_freelancer-layout/")({
  component: FreelancerDashboard,
  head: () => ({
    meta: [{ title: "Dashboard - Freelancer Portal" }],
  }),
})

// Format currency
function formatCurrency(amount: string | number) {
  const num = typeof amount === "string" ? Number.parseFloat(amount) : amount
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num)
}

// Stats Card Component
function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = "primary",
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  color?: "primary" | "green" | "yellow" | "blue" | "red"
}) {
  const colorClasses = {
    primary: "bg-primary/10 text-primary",
    green: "bg-green-500/10 text-green-600 dark:text-green-400",
    yellow: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400",
    blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
    red: "bg-red-500/10 text-red-600 dark:text-red-400",
  }

  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className={`rounded-lg p-2 ${colorClasses[color]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    </div>
  )
}

function DashboardContent() {
  const { freelancer } = useFreelancerAuth()

  const { data: stats, isLoading } = useQuery({
    queryKey: ["freelancer", "dashboard", "stats"],
    queryFn: () => FreelancerPortalService.getDashboardStats(),
  })

  if (isLoading || !stats) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="rounded-lg bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-6">
        <h2 className="text-xl font-semibold">
          Welcome back, {freelancer?.name?.split(" ")[0]}!
        </h2>
        <p className="text-muted-foreground mt-1">
          Here's an overview of your work and earnings.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total WorkLogs"
          value={stats.total_worklogs}
          subtitle="All time"
          icon={Calendar}
        />
        <StatsCard
          title="Total Hours"
          value={`${Number.parseFloat(stats.total_hours_logged).toFixed(1)}h`}
          subtitle="Hours logged"
          icon={Clock}
          color="blue"
        />
        <StatsCard
          title="Total Earned"
          value={formatCurrency(stats.total_earned)}
          subtitle="Paid to date"
          icon={DollarSign}
          color="green"
        />
        <StatsCard
          title="Pending Amount"
          value={formatCurrency(stats.pending_amount)}
          subtitle="Awaiting payment"
          icon={AlertCircle}
          color="yellow"
        />
      </div>

      {/* Status Breakdown */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-yellow-500/10 p-2">
                <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.pending_worklogs}</p>
                <p className="text-sm text-muted-foreground">Pending Review</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-500/10 p-2">
                <CheckCircle2 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.approved_worklogs}</p>
                <p className="text-sm text-muted-foreground">Approved</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-500/10 p-2">
                <DollarSign className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.paid_worklogs}</p>
                <p className="text-sm text-muted-foreground">Paid</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-500/10 p-2">
                <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.rejected_worklogs}</p>
                <p className="text-sm text-muted-foreground">Rejected</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Your Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-primary">
            {formatCurrency(freelancer?.hourly_rate || "0")}
            <span className="text-lg font-normal text-muted-foreground">
              /hour
            </span>
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            This is your current hourly rate. You can update it in your profile
            settings.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

function FreelancerDashboard() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your work and earnings
        </p>
      </div>
      <Suspense fallback={<DashboardSkeleton />}>
        <DashboardContent />
      </Suspense>
    </div>
  )
}
