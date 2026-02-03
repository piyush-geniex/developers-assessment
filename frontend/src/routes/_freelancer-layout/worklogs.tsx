import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import {
  CheckCircle2,
  Clock,
  DollarSign,
  Plus,
  Search,
  XCircle,
  AlertCircle,
  ChevronRight,
  Trash2,
} from "lucide-react"
import { Suspense, useState, useMemo } from "react"

import {
  FreelancerPortalService,
  type WorkLogStatus,
  type WorkLogSummary,
} from "@/client/freelancerPortalService"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { cn } from "@/lib/utils"
import { formatCurrency, formatDuration, formatDate } from "@/lib/formatters"
import useCustomToast from "@/hooks/useCustomToast"
import CreateWorkLogDialog from "@/components/FreelancerPortal/CreateWorkLogDialog"
import FreelancerWorkLogDetailSheet from "@/components/FreelancerPortal/WorkLogDetailSheet"

export const Route = (createFileRoute as any)("/_freelancer-layout/worklogs")({
  component: FreelancerWorkLogs,
  head: () => ({
    meta: [{ title: "My WorkLogs - Freelancer Portal" }],
  }),
})

// Status badge config
const statusConfig: Record<
  WorkLogStatus,
  {
    label: string
    variant: "default" | "secondary" | "destructive" | "outline"
    icon: React.ElementType
  }
> = {
  pending: { label: "Pending", variant: "secondary", icon: Clock },
  approved: { label: "Approved", variant: "default", icon: CheckCircle2 },
  paid: { label: "Paid", variant: "outline", icon: DollarSign },
  rejected: { label: "Rejected", variant: "destructive", icon: XCircle },
}

function WorkLogsSkeleton() {
  return (
    <div className="space-y-4">
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
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // State
  const [statusFilter, setStatusFilter] = useState<WorkLogStatus | "all">("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [selectedWorklogId, setSelectedWorklogId] = useState<string | null>(null)
  const [deleteWorklogId, setDeleteWorklogId] = useState<string | null>(null)

  // Query
  const { data: worklogsData, isLoading } = useQuery({
    queryKey: ["freelancer", "worklogs", statusFilter],
    queryFn: () =>
      FreelancerPortalService.getMyWorklogs({
        limit: 200,
        status: statusFilter === "all" ? undefined : [statusFilter],
      }),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => FreelancerPortalService.deleteWorklog(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklogs"] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "dashboard"] })
      showSuccessToast("WorkLog deleted successfully")
      setDeleteWorklogId(null)
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to delete worklog")
    },
  })

  // Filter by search
  const filteredWorklogs = useMemo(() => {
    if (!worklogsData?.data) return []
    if (!searchQuery) return worklogsData.data

    const query = searchQuery.toLowerCase()
    return worklogsData.data.filter((wl: WorkLogSummary) =>
      wl.task_description.toLowerCase().includes(query)
    )
  }, [worklogsData?.data, searchQuery])

  if (isLoading) {
    return <WorkLogsSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-1 flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative flex-1 min-w-[200px] max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search tasks..."
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
            </div>

            {/* Create Button */}
            <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              New WorkLog
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* WorkLogs Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Task</TableHead>
                <TableHead className="text-center">Entries</TableHead>
                <TableHead className="text-right">Duration</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-center">Status</TableHead>
                <TableHead className="text-right">Date</TableHead>
                <TableHead className="w-24" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredWorklogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center">
                    <div className="flex flex-col items-center justify-center text-muted-foreground">
                      <AlertCircle className="h-8 w-8 mb-2" />
                      <p>No worklogs found</p>
                      <p className="text-sm">
                        {statusFilter !== "all"
                          ? "Try changing the filter"
                          : "Create your first worklog to get started"}
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredWorklogs.map((worklog: WorkLogSummary) => {
                  const config = statusConfig[worklog.status as WorkLogStatus]
                  const StatusIcon = config.icon
                  const canEdit = worklog.status === "pending"

                  return (
                    <TableRow
                      key={worklog.id}
                      className={cn(
                        "cursor-pointer transition-colors",
                        worklog.status === "paid" && "opacity-60"
                      )}
                      onClick={() => setSelectedWorklogId(worklog.id)}
                    >
                      <TableCell>
                        <div className="max-w-[300px]">
                          <p className="font-medium truncate">
                            {worklog.task_description}
                          </p>
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
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1">
                          {canEdit && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive"
                              onClick={() => setDeleteWorklogId(worklog.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <CreateWorkLogDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />

      {/* Detail Sheet */}
      <FreelancerWorkLogDetailSheet
        worklogId={selectedWorklogId}
        open={!!selectedWorklogId}
        onOpenChange={(open) => !open && setSelectedWorklogId(null)}
      />

      {/* Delete Confirmation */}
      <AlertDialog
        open={!!deleteWorklogId}
        onOpenChange={(open) => !open && setDeleteWorklogId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete WorkLog?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this worklog and all its time entries.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deleteWorklogId && deleteMutation.mutate(deleteWorklogId)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

function FreelancerWorkLogs() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">My WorkLogs</h1>
        <p className="text-muted-foreground">
          Track and manage your work hours
        </p>
      </div>
      <Suspense fallback={<WorkLogsSkeleton />}>
        <WorkLogsContent />
      </Suspense>
    </div>
  )
}
