import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  Filter,
  Search,
  Users,
  XCircle,
  AlertCircle,
  CreditCard,
  ChevronRight,
} from "lucide-react"
import { Suspense, useState, useMemo, useCallback } from "react"

import {
  WorkLogsService,
  FreelancersService,
  type WorkLogStatus,
} from "@/client/worklogService"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { formatCurrency, formatDuration, formatDate } from "@/lib/formatters"
import WorkLogDetailSheet from "@/components/WorkLogs/WorkLogDetailSheet"

export const Route = createFileRoute("/_layout/worklogs" as any)({
  component: WorkLogs,
  head: () => ({
    meta: [
      {
        title: "WorkLogs - Payment Dashboard",
      },
    ],
  }),
})

// Status badge colors
const statusConfig: Record<
  WorkLogStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline"; icon: React.ElementType }
> = {
  pending: { label: "Pending", variant: "secondary", icon: Clock },
  approved: { label: "Approved", variant: "default", icon: CheckCircle2 },
  paid: { label: "Paid", variant: "outline", icon: DollarSign },
  rejected: { label: "Rejected", variant: "destructive", icon: XCircle },
}

// Stats Card Component
function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="rounded-lg bg-primary/10 p-2">
          <Icon className="h-4 w-4 text-primary" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary/20 via-primary/40 to-primary/20" />
    </Card>
  )
}

// Loading skeleton for the table
function WorkLogsTableSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <Skeleton className="h-12 w-full" />
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    </div>
  )
}

function WorkLogsContent() {
  const navigate = useNavigate()

  // State
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [statusFilter, setStatusFilter] = useState<WorkLogStatus | "all">("all")
  const [freelancerFilter, setFreelancerFilter] = useState<string>("all")
  const [dateFrom, setDateFrom] = useState<string>("")
  const [dateTo, setDateTo] = useState<string>("")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedWorklogId, setSelectedWorklogId] = useState<string | null>(null)

  // Queries
  const { data: worklogsData, isLoading: worklogsLoading } = useQuery({
    queryKey: [
      "worklogs",
      "summary",
      statusFilter,
      freelancerFilter,
      dateFrom,
      dateTo,
    ],
    queryFn: () =>
      WorkLogsService.getWorklogsSummary({
        limit: 200,
        status: statusFilter === "all" ? undefined : [statusFilter],
        freelancerId: freelancerFilter === "all" ? undefined : freelancerFilter,
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
      }),
  })

  const { data: freelancersData } = useQuery({
    queryKey: ["freelancers"],
    queryFn: () => FreelancersService.getFreelancers({ limit: 100 }),
  })

  // Filter by search query
  const filteredWorklogs = useMemo(() => {
    if (!worklogsData?.data) return []
    if (!searchQuery) return worklogsData.data

    const query = searchQuery.toLowerCase()
    return worklogsData.data.filter(
      (wl) =>
        wl.task_description.toLowerCase().includes(query) ||
        wl.freelancer_name.toLowerCase().includes(query)
    )
  }, [worklogsData?.data, searchQuery])

  // Calculate stats
  const stats = useMemo(() => {
    if (!filteredWorklogs.length) {
      return {
        totalWorklogs: 0,
        totalAmount: 0,
        totalHours: 0,
        pendingCount: 0,
      }
    }

    const payableWorklogs = filteredWorklogs.filter(
      (wl) => wl.status === "pending" || wl.status === "approved"
    )

    return {
      totalWorklogs: filteredWorklogs.length,
      totalAmount: payableWorklogs.reduce(
        (sum, wl) => sum + Number.parseFloat(wl.total_amount),
        0
      ),
      totalHours: Math.round(
        payableWorklogs.reduce((sum, wl) => sum + wl.total_duration_minutes, 0) / 60
      ),
      pendingCount: filteredWorklogs.filter((wl) => wl.status === "pending")
        .length,
    }
  }, [filteredWorklogs])

  // Memoized selection handlers to prevent unnecessary re-renders
  const handleSelectAll = useCallback((checked: boolean) => {
    if (checked) {
      const payableIds = filteredWorklogs
        .filter((wl) => wl.status !== "paid" && wl.status !== "rejected")
        .map((wl) => wl.id)
      setSelectedIds(new Set(payableIds))
    } else {
      setSelectedIds(new Set())
    }
  }, [filteredWorklogs])

  const handleSelectOne = useCallback((id: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const newSelected = new Set(prev)
      if (checked) {
        newSelected.add(id)
      } else {
        newSelected.delete(id)
      }
      return newSelected
    })
  }, [])

  // Get selected worklogs for summary
  const selectedWorklogs = filteredWorklogs.filter((wl) =>
    selectedIds.has(wl.id)
  )
  const selectedTotal = selectedWorklogs.reduce(
    (sum, wl) => sum + Number.parseFloat(wl.total_amount),
    0
  )

  // Navigate to payment review
  const handleProcessPayment = () => {
    const ids = Array.from(selectedIds).join(",")
    navigate({ to: "/payment-review" as any, search: { ids } as any })
  }

  const payableWorklogs = filteredWorklogs.filter(
    (wl) => wl.status !== "paid" && wl.status !== "rejected"
  )
  const allPayableSelected =
    payableWorklogs.length > 0 &&
    payableWorklogs.every((wl) => selectedIds.has(wl.id))

  if (worklogsLoading) {
    return <WorkLogsTableSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total WorkLogs"
          value={stats.totalWorklogs}
          subtitle="In current view"
          icon={Calendar}
        />
        <StatsCard
          title="Pending Review"
          value={stats.pendingCount}
          subtitle="Awaiting approval"
          icon={AlertCircle}
        />
        <StatsCard
          title="Total Hours"
          value={`${stats.totalHours}h`}
          subtitle="Payable worklogs"
          icon={Clock}
        />
        <StatsCard
          title="Payable Amount"
          value={formatCurrency(stats.totalAmount)}
          subtitle="Pending + Approved"
          icon={DollarSign}
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-1 flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative flex-1 min-w-[200px] max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search tasks or freelancers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>

              {/* Status Filter */}
              <Select
                value={statusFilter}
                onValueChange={(v) => setStatusFilter(v as WorkLogStatus | "all")}
              >
                <SelectTrigger className="w-[140px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>

              {/* Freelancer Filter */}
              <Select
                value={freelancerFilter}
                onValueChange={setFreelancerFilter}
              >
                <SelectTrigger className="w-[180px]">
                  <Users className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Freelancer" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Freelancers</SelectItem>
                  {freelancersData?.data.map((f) => (
                    <SelectItem key={f.id} value={f.id}>
                      {f.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Date Range */}
              <div className="flex items-center gap-2">
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-[140px]"
                  placeholder="From"
                />
                <span className="text-muted-foreground">to</span>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-[140px]"
                  placeholder="To"
                />
              </div>
            </div>

            {/* Process Payment Button */}
            {selectedIds.size > 0 && (
              <div className="flex items-center gap-4">
                <div className="text-sm">
                  <span className="text-muted-foreground">Selected: </span>
                  <span className="font-semibold">{selectedIds.size} items</span>
                  <span className="mx-2 text-muted-foreground">|</span>
                  <span className="font-semibold text-primary">
                    {formatCurrency(selectedTotal)}
                  </span>
                </div>
                <Button onClick={handleProcessPayment} className="gap-2">
                  <CreditCard className="h-4 w-4" />
                  Process Payment
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* WorkLogs Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-12">
                  <Checkbox
                    checked={allPayableSelected}
                    onCheckedChange={handleSelectAll}
                    aria-label="Select all"
                  />
                </TableHead>
                <TableHead>Task</TableHead>
                <TableHead>Freelancer</TableHead>
                <TableHead className="text-center">Entries</TableHead>
                <TableHead className="text-right">Duration</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-center">Status</TableHead>
                <TableHead className="text-right">Date</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredWorklogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="h-32 text-center">
                    <div className="flex flex-col items-center justify-center text-muted-foreground">
                      <Search className="h-8 w-8 mb-2" />
                      <p>No worklogs found</p>
                      <p className="text-sm">
                        Try adjusting your filters
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredWorklogs.map((worklog) => {
                  const config = statusConfig[worklog.status]
                  const StatusIcon = config.icon
                  const isPayable =
                    worklog.status !== "paid" && worklog.status !== "rejected"
                  const isSelected = selectedIds.has(worklog.id)

                  return (
                    <TableRow
                      key={worklog.id}
                      className={cn(
                        "cursor-pointer transition-colors",
                        isSelected && "bg-primary/5",
                        worklog.status === "paid" && "opacity-60"
                      )}
                      onClick={() => setSelectedWorklogId(worklog.id)}
                    >
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={(checked) =>
                            handleSelectOne(worklog.id, checked as boolean)
                          }
                          disabled={!isPayable}
                          aria-label={`Select ${worklog.task_description}`}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="max-w-[300px]">
                          <p className="font-medium truncate">
                            {worklog.task_description}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center">
                            <span className="text-xs font-semibold text-primary">
                              {worklog.freelancer_name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </span>
                          </div>
                          <div>
                            <p className="text-sm font-medium">
                              {worklog.freelancer_name}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatCurrency(worklog.hourly_rate)}/hr
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex items-center justify-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                          {worklog.time_entry_count}
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {formatDuration(worklog.total_duration_minutes)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="font-semibold">
                          {formatCurrency(worklog.total_amount)}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant={config.variant} className="gap-1">
                          <StatusIcon className="h-3 w-3" />
                          {config.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">
                        {formatDate(worklog.created_at)}
                      </TableCell>
                      <TableCell>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Detail Sheet */}
      <WorkLogDetailSheet
        worklogId={selectedWorklogId}
        open={!!selectedWorklogId}
        onOpenChange={(open) => !open && setSelectedWorklogId(null)}
      />
    </div>
  )
}

function WorkLogs() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">WorkLog Dashboard</h1>
        <p className="text-muted-foreground">
          Review and process freelancer payments
        </p>
      </div>
      <Suspense fallback={<WorkLogsTableSkeleton />}>
        <WorkLogsContent />
      </Suspense>
    </div>
  )
}
