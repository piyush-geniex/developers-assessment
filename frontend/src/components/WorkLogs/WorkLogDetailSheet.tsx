import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  Mail,
  User,
  XCircle,
  AlertCircle,
  FileText,
  ArrowRight,
} from "lucide-react"

import {
  WorkLogsService,
  type WorkLogStatus,
  type TimeEntryPublic,
} from "@/client/worklogService"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"

interface WorkLogDetailSheetProps {
  worklogId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

// Status configuration
const statusConfig: Record<
  WorkLogStatus,
  {
    label: string
    variant: "default" | "secondary" | "destructive" | "outline"
    icon: React.ElementType
    color: string
  }
> = {
  pending: {
    label: "Pending Review",
    variant: "secondary",
    icon: Clock,
    color: "text-yellow-600",
  },
  approved: {
    label: "Approved",
    variant: "default",
    icon: CheckCircle2,
    color: "text-green-600",
  },
  paid: {
    label: "Paid",
    variant: "outline",
    icon: DollarSign,
    color: "text-blue-600",
  },
  rejected: {
    label: "Rejected",
    variant: "destructive",
    icon: XCircle,
    color: "text-red-600",
  },
}

// Allowed transitions
const allowedTransitions: Record<WorkLogStatus, WorkLogStatus[]> = {
  pending: ["approved", "rejected"],
  approved: ["pending", "rejected"],
  rejected: ["pending"],
  paid: [],
}

// Format helpers
function formatCurrency(amount: string | number) {
  const num = typeof amount === "string" ? Number.parseFloat(amount) : amount
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num)
}

function formatDuration(minutes: number) {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours === 0) return `${mins}m`
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}m`
}

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

function formatTime(dateString: string) {
  return new Date(dateString).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  })
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  })
}

// Time Entry Row Component
function TimeEntryRow({ entry }: { entry: TimeEntryPublic }) {
  return (
    <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
      <div className="flex items-center gap-4">
        <div className="flex flex-col">
          <span className="text-sm font-medium">
            {formatDate(entry.start_time)}
          </span>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <span>{formatTime(entry.start_time)}</span>
            <ArrowRight className="h-3 w-3" />
            <span>{formatTime(entry.end_time)}</span>
          </div>
        </div>
        {entry.notes && (
          <span className="text-sm text-muted-foreground max-w-[200px] truncate">
            {entry.notes}
          </span>
        )}
      </div>
      <div className="text-right">
        <span className="font-mono text-sm font-semibold">
          {formatDuration(entry.duration_minutes)}
        </span>
      </div>
    </div>
  )
}

// Loading Skeleton
function DetailSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <Skeleton className="h-8 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <div className="grid grid-cols-2 gap-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-32" />
      <div className="space-y-2">
        <Skeleton className="h-16" />
        <Skeleton className="h-16" />
        <Skeleton className="h-16" />
      </div>
    </div>
  )
}

export default function WorkLogDetailSheet({
  worklogId,
  open,
  onOpenChange,
}: WorkLogDetailSheetProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Fetch worklog detail
  const { data: worklog, isLoading } = useQuery({
    queryKey: ["worklog", "detail", worklogId],
    queryFn: () => WorkLogsService.getWorklogDetail({ worklogId: worklogId! }),
    enabled: !!worklogId && open,
  })

  // Status update mutation
  const statusMutation = useMutation({
    mutationFn: (newStatus: WorkLogStatus) =>
      WorkLogsService.updateWorklogStatus({
        worklogId: worklogId!,
        status: newStatus,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["worklogs"] })
      queryClient.invalidateQueries({ queryKey: ["worklog", "detail", worklogId] })
      showSuccessToast("Status updated successfully")
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to update status")
    },
  })

  if (!worklogId) return null

  const config = worklog ? statusConfig[worklog.status] : null
  const transitions = worklog ? allowedTransitions[worklog.status] : []

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
        {isLoading || !worklog ? (
          <DetailSkeleton />
        ) : (
          <>
            <SheetHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <SheetTitle className="text-xl leading-tight">
                    {worklog.task_description}
                  </SheetTitle>
                  <SheetDescription className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    {formatDateTime(worklog.created_at)}
                  </SheetDescription>
                </div>
                {config && (
                  <Badge variant={config.variant} className="gap-1">
                    <config.icon className="h-3 w-3" />
                    {config.label}
                  </Badge>
                )}
              </div>
            </SheetHeader>

            <Separator />

            <div className="py-6 space-y-6">
              {/* Freelancer Info */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <User className="h-4 w-4" />
                    Freelancer
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary/30 to-primary/10 flex items-center justify-center">
                      <span className="text-lg font-bold text-primary">
                        {worklog.freelancer.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")}
                      </span>
                    </div>
                    <div>
                      <p className="font-semibold">{worklog.freelancer.name}</p>
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Mail className="h-3 w-3" />
                        {worklog.freelancer.email}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <span className="text-sm text-muted-foreground">
                      Hourly Rate
                    </span>
                    <span className="font-semibold">
                      {formatCurrency(worklog.freelancer.hourly_rate)}/hr
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Summary Stats */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-blue-100 dark:bg-blue-900/30 p-2">
                        <Clock className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">
                          Total Time
                        </p>
                        <p className="text-xl font-bold">
                          {formatDuration(worklog.total_duration_minutes)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-green-100 dark:bg-green-900/30 p-2">
                        <DollarSign className="h-5 w-5 text-green-600 dark:text-green-400" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">
                          Total Amount
                        </p>
                        <p className="text-xl font-bold">
                          {formatCurrency(worklog.total_amount)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Time Entries */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Time Entries
                    </span>
                    <Badge variant="secondary">
                      {worklog.time_entries.length} entries
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {worklog.time_entries.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>No time entries recorded</p>
                    </div>
                  ) : (
                    worklog.time_entries.map((entry) => (
                      <TimeEntryRow key={entry.id} entry={entry} />
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Status Actions */}
              {transitions.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium">
                      Actions
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-wrap gap-2">
                    {transitions.includes("approved") && (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => statusMutation.mutate("approved")}
                        disabled={statusMutation.isPending}
                        className="gap-1"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        Approve
                      </Button>
                    )}
                    {transitions.includes("pending") && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => statusMutation.mutate("pending")}
                        disabled={statusMutation.isPending}
                        className="gap-1"
                      >
                        <Clock className="h-4 w-4" />
                        Move to Pending
                      </Button>
                    )}
                    {transitions.includes("rejected") && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => statusMutation.mutate("rejected")}
                        disabled={statusMutation.isPending}
                        className="gap-1"
                      >
                        <XCircle className="h-4 w-4" />
                        Reject
                      </Button>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
