import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  CreditCard,
  DollarSign,
  Loader2,
  Mail,
  Trash2,
  User,
  Users,
  XCircle,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  PartyPopper,
} from "lucide-react"
import { useState, useMemo } from "react"

import {
  PaymentsService,
  type FreelancerPaymentSummary,
  type PaymentIssue,
} from "@/client/worklogService"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { formatCurrency, formatDuration, parseAndValidateIds } from "@/lib/formatters"

export const Route = createFileRoute("/_layout/payment-review" as any)({
  component: PaymentReview,
})

// Freelancer Breakdown Card
function FreelancerCard({
  freelancer,
  excludedIds,
  onExclude,
}: {
  freelancer: FreelancerPaymentSummary
  excludedIds: Set<string>
  onExclude: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)

  const activeWorklogs = freelancer.worklogs.filter(
    (wl) => !excludedIds.has(wl.id)
  )
  const activeAmount = activeWorklogs.reduce(
    (sum, wl) => sum + Number.parseFloat(wl.total_amount),
    0
  )
  const activeDuration = activeWorklogs.reduce(
    (sum, wl) => sum + wl.total_duration_minutes,
    0
  )
  const allExcluded = activeWorklogs.length === 0

  return (
    <Card className={cn(allExcluded && "opacity-50")}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary/30 to-primary/10 flex items-center justify-center">
              <span className="text-sm font-bold text-primary">
                {freelancer.freelancer_name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </span>
            </div>
            <div>
              <CardTitle className="text-base">
                {freelancer.freelancer_name}
              </CardTitle>
              <CardDescription className="flex items-center gap-1">
                <Mail className="h-3 w-3" />
                {freelancer.freelancer_email}
              </CardDescription>
            </div>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold">
              {allExcluded ? (
                <span className="text-muted-foreground line-through">
                  {formatCurrency(freelancer.total_amount)}
                </span>
              ) : (
                formatCurrency(activeAmount)
              )}
            </p>
            <p className="text-sm text-muted-foreground">
              {activeWorklogs.length} worklog
              {activeWorklogs.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between py-2 px-3 rounded-lg bg-muted/50 mb-3">
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Clock className="h-4 w-4" />
              {formatDuration(activeDuration)}
            </span>
            <span className="flex items-center gap-1 text-muted-foreground">
              <DollarSign className="h-4 w-4" />
              {formatCurrency(freelancer.hourly_rate)}/hr
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="gap-1"
          >
            {expanded ? (
              <>
                <ChevronUp className="h-4 w-4" />
                Hide
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" />
                Show Items
              </>
            )}
          </Button>
        </div>

        {expanded && (
          <div className="space-y-2">
            {freelancer.worklogs.map((worklog) => {
              const isExcluded = excludedIds.has(worklog.id)
              return (
                <div
                  key={worklog.id}
                  className={cn(
                    "flex items-center justify-between py-2 px-3 rounded-lg border transition-all",
                    isExcluded
                      ? "bg-muted/30 opacity-50"
                      : "bg-background hover:bg-muted/30"
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <p
                      className={cn(
                        "text-sm font-medium truncate",
                        isExcluded && "line-through"
                      )}
                    >
                      {worklog.task_description}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDuration(worklog.total_duration_minutes)} •{" "}
                      {formatCurrency(worklog.total_amount)}
                    </p>
                  </div>
                  <Button
                    variant={isExcluded ? "outline" : "ghost"}
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={() => onExclude(worklog.id)}
                  >
                    {isExcluded ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <Trash2 className="h-4 w-4 text-destructive" />
                    )}
                  </Button>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Issues Alert
function IssuesAlert({ issues }: { issues: PaymentIssue[] }) {
  if (issues.length === 0) return null

  const warningIssues = issues.filter((i) => i.issue_type === "ZERO_DURATION")
  const errorIssues = issues.filter((i) => i.issue_type !== "ZERO_DURATION")

  return (
    <div className="space-y-3">
      {errorIssues.length > 0 && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertTitle>Cannot Process</AlertTitle>
          <AlertDescription>
            <ul className="mt-2 space-y-1">
              {errorIssues.map((issue, i) => (
                <li key={i} className="text-sm">
                  {issue.message}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
      {warningIssues.length > 0 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Warnings</AlertTitle>
          <AlertDescription>
            <ul className="mt-2 space-y-1">
              {warningIssues.map((issue, i) => (
                <li key={i} className="text-sm">
                  {issue.message}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

// Success Dialog
function SuccessDialog({
  open,
  result,
  onClose,
}: {
  open: boolean
  result: { batch_id: string; total_worklogs: number; total_amount: string } | null
  onClose: () => void
}) {
  const navigate = useNavigate()

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <PartyPopper className="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
          <DialogTitle className="text-center text-xl">
            Payment Processed!
          </DialogTitle>
          <DialogDescription className="text-center">
            {result && (
              <>
                Successfully processed payment for{" "}
                <span className="font-semibold">{result.total_worklogs}</span>{" "}
                worklog{result.total_worklogs !== 1 ? "s" : ""} totaling{" "}
                <span className="font-semibold text-primary">
                  {formatCurrency(result.total_amount)}
                </span>
              </>
            )}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="flex-col gap-2 sm:flex-col">
          <Button
            className="w-full"
            onClick={() => navigate({ to: "/worklogs" as any })}
          >
            Back to Dashboard
          </Button>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => navigate({ to: "/payment-history" as any })}
          >
            View Payment History
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Loading skeleton
function ReviewSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-48" />
      <Skeleton className="h-48" />
    </div>
  )
}

function PaymentReview() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()
  const searchParams = useSearch({ strict: false }) as { ids?: string }
  const ids = searchParams.ids || ""

  // Parse and validate worklog IDs from URL
  const worklogIds = useMemo(() => {
    return parseAndValidateIds(ids)
  }, [ids])

  // State
  const [excludedIds, setExcludedIds] = useState<Set<string>>(new Set())
  const [notes, setNotes] = useState("")
  const [showConfirm, setShowConfirm] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [processResult, setProcessResult] = useState<{
    batch_id: string
    total_worklogs: number
    total_amount: string
  } | null>(null)

  // Fetch preview
  const { data: preview, isLoading, error } = useQuery({
    queryKey: ["payment", "preview", worklogIds],
    queryFn: () => PaymentsService.previewPayment({ worklogIds }),
    enabled: worklogIds.length > 0,
  })

  // Process mutation
  const processMutation = useMutation({
    mutationFn: (activeIds: string[]) =>
      PaymentsService.processPayment({ worklogIds: activeIds, notes: notes || undefined }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["worklogs"] })
      setProcessResult(data)
      setShowConfirm(false)
      setShowSuccess(true)
    },
    onError: (error: any) => {
      showErrorToast(error.body?.detail || "Failed to process payment")
      setShowConfirm(false)
    },
  })

  // Calculate active amounts
  const activeBreakdown = useMemo(() => {
    if (!preview) return { freelancers: [], totalAmount: 0, totalWorklogs: 0, totalDuration: 0 }

    const freelancers = preview.freelancer_breakdown.map((fb) => {
      const activeWorklogs = fb.worklogs.filter((wl) => !excludedIds.has(wl.id))
      return {
        ...fb,
        activeWorklogs,
        activeAmount: activeWorklogs.reduce(
          (sum, wl) => sum + Number.parseFloat(wl.total_amount),
          0
        ),
        activeDuration: activeWorklogs.reduce(
          (sum, wl) => sum + wl.total_duration_minutes,
          0
        ),
      }
    }).filter((fb) => fb.activeWorklogs.length > 0)

    return {
      freelancers,
      totalAmount: freelancers.reduce((sum, fb) => sum + fb.activeAmount, 0),
      totalWorklogs: freelancers.reduce(
        (sum, fb) => sum + fb.activeWorklogs.length,
        0
      ),
      totalDuration: freelancers.reduce((sum, fb) => sum + fb.activeDuration, 0),
    }
  }, [preview, excludedIds])

  // Get active worklog IDs
  const activeWorklogIds = useMemo(() => {
    if (!preview) return []
    return preview.freelancer_breakdown
      .flatMap((fb) => fb.worklogs)
      .filter((wl) => !excludedIds.has(wl.id))
      .map((wl) => wl.id)
  }, [preview, excludedIds])

  // Toggle exclude
  const handleExclude = (id: string) => {
    const newExcluded = new Set(excludedIds)
    if (newExcluded.has(id)) {
      newExcluded.delete(id)
    } else {
      newExcluded.add(id)
    }
    setExcludedIds(newExcluded)
  }

  // Handle process
  const handleProcess = () => {
    processMutation.mutate(activeWorklogIds)
  }

  if (worklogIds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold mb-2">No Items Selected</h2>
        <p className="text-muted-foreground mb-4">
          Please select worklogs from the dashboard to process payment.
        </p>
        <Button onClick={() => navigate({ to: "/worklogs" as any })}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>
    )
  }

  if (isLoading) {
    return <ReviewSkeleton />
  }

  if (error || !preview) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <XCircle className="h-12 w-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">Failed to Load Preview</h2>
        <p className="text-muted-foreground mb-4">
          Something went wrong while loading the payment preview.
        </p>
        <Button onClick={() => navigate({ to: "/worklogs" as any })}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate({ to: "/worklogs" as any })}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Review Payment</h1>
          <p className="text-muted-foreground">
            Review and confirm the payment batch
          </p>
        </div>
      </div>

      {/* Issues */}
      <IssuesAlert issues={preview.issues} />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 dark:bg-blue-900/30 p-3">
                <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Freelancers</p>
                <p className="text-2xl font-bold">
                  {activeBreakdown.freelancers.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 dark:bg-purple-900/30 p-3">
                <Clock className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Hours</p>
                <p className="text-2xl font-bold">
                  {formatDuration(activeBreakdown.totalDuration)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-primary/20 p-3">
                <DollarSign className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Amount</p>
                <p className="text-2xl font-bold text-primary">
                  {formatCurrency(activeBreakdown.totalAmount)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Freelancer Breakdown */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <User className="h-5 w-5" />
          Payment Breakdown
          <Badge variant="secondary">{activeBreakdown.totalWorklogs} items</Badge>
        </h2>

        {preview.freelancer_breakdown.map((freelancer) => (
          <FreelancerCard
            key={freelancer.freelancer_id}
            freelancer={freelancer}
            excludedIds={excludedIds}
            onExclude={handleExclude}
          />
        ))}
      </div>

      {/* Notes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Payment Notes (Optional)</CardTitle>
          <CardDescription>
            Add any notes for this payment batch
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Input
            placeholder="e.g., October 1-15 Payment Cycle"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="outline" onClick={() => navigate({ to: "/worklogs" as any })}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Cancel
        </Button>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-muted-foreground">
              {activeBreakdown.totalWorklogs} worklog
              {activeBreakdown.totalWorklogs !== 1 ? "s" : ""}
            </p>
            <p className="text-lg font-bold text-primary">
              {formatCurrency(activeBreakdown.totalAmount)}
            </p>
          </div>
          <Button
            size="lg"
            disabled={activeBreakdown.totalWorklogs === 0 || !preview.can_process}
            onClick={() => setShowConfirm(true)}
            className="gap-2"
          >
            <CreditCard className="h-5 w-5" />
            Confirm Payment
          </Button>
        </div>
      </div>

      {/* Confirm Dialog */}
      <Dialog open={showConfirm} onOpenChange={setShowConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Payment</DialogTitle>
            <DialogDescription>
              You are about to process a payment of{" "}
              <span className="font-semibold text-primary">
                {formatCurrency(activeBreakdown.totalAmount)}
              </span>{" "}
              to {activeBreakdown.freelancers.length} freelancer
              {activeBreakdown.freelancers.length !== 1 ? "s" : ""} for{" "}
              {activeBreakdown.totalWorklogs} worklog
              {activeBreakdown.totalWorklogs !== 1 ? "s" : ""}.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirm(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleProcess}
              disabled={processMutation.isPending}
            >
              {processMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                "Confirm"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Dialog */}
      <SuccessDialog
        open={showSuccess}
        result={processResult}
        onClose={() => {
          setShowSuccess(false)
          navigate({ to: "/worklogs" as any })
        }}
      />
    </div>
  )
}
