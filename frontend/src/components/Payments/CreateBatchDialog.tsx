import { useMutation, useQueryClient } from "@tanstack/react-query"
import { PlusCircle } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import type { EligibleEntry, PaymentBatchDetail } from "@/client"
import { PaymentsService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type Step = "date_range" | "review" | "confirm"

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

// Step 1 — pick date range
function StepDateRange({
  dateFrom,
  dateTo,
  onChange,
  onNext,
  isLoading,
}: {
  dateFrom: string
  dateTo: string
  onChange: (from: string, to: string) => void
  onNext: () => void
  isLoading: boolean
}) {
  return (
    <div className="flex flex-col gap-6 py-4">
      <p className="text-sm text-muted-foreground">
        Select the date range for this payment cycle. All time entries logged
        within this period (and not yet paid) will be included.
      </p>
      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor="batch-date-from">From</Label>
          <Input
            id="batch-date-from"
            type="date"
            value={dateFrom}
            onChange={(e) => onChange(e.target.value, dateTo)}
            aria-label="Payment period start date"
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="batch-date-to">To</Label>
          <Input
            id="batch-date-to"
            type="date"
            value={dateTo}
            onChange={(e) => onChange(dateFrom, e.target.value)}
            aria-label="Payment period end date"
          />
        </div>
      </div>
      <DialogFooter>
        <Button
          onClick={onNext}
          disabled={!dateFrom || !dateTo || isLoading}
          aria-label="Preview eligible worklogs"
        >
          {isLoading ? "Loading…" : "Preview Worklogs"}
        </Button>
      </DialogFooter>
    </div>
  )
}

// Step 2 — review eligible entries
function StepReview({
  batch,
  excludedWorklogs,
  excludedFreelancers,
  onToggleWorklog,
  onToggleFreelancer,
  onBack,
  onNext,
}: {
  batch: PaymentBatchDetail
  excludedWorklogs: Set<string>
  excludedFreelancers: Set<string>
  onToggleWorklog: (id: string) => void
  onToggleFreelancer: (id: string) => void
  onBack: () => void
  onNext: () => void
}) {
  const included = batch.eligible_entries.filter(
    (e) =>
      !excludedWorklogs.has(e.worklog_id) &&
      !excludedFreelancers.has(e.freelancer_id),
  )
  const totalAmount = included.reduce((sum, e) => sum + e.amount, 0)
  const totalHours = included.reduce((sum, e) => sum + e.hours, 0)

  // Group entries by worklog to show one row per worklog
  const byWorklog = new Map<string, EligibleEntry[]>()
  for (const entry of batch.eligible_entries) {
    const existing = byWorklog.get(entry.worklog_id) ?? []
    existing.push(entry)
    byWorklog.set(entry.worklog_id, existing)
  }

  return (
    <div className="flex flex-col gap-4 py-2">
      <p className="text-sm text-muted-foreground">
        Review eligible worklogs for{" "}
        <span className="font-medium text-foreground">
          {formatDate(batch.date_from)} – {formatDate(batch.date_to)}
        </span>
        . Uncheck worklogs or freelancers to exclude them from this payment.
      </p>

      {batch.eligible_entries.length === 0 ? (
        <div className="py-8 text-center text-sm text-muted-foreground">
          No eligible time entries found for this date range.
        </div>
      ) : (
        <div className="max-h-80 overflow-y-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-8">
                  <span className="sr-only">Include worklog</span>
                </TableHead>
                <TableHead>Worklog</TableHead>
                <TableHead>Freelancer</TableHead>
                <TableHead className="text-right">Hours</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Array.from(byWorklog.entries()).map(([worklogId, entries]) => {
                const first = entries[0]
                const wlHours = entries.reduce((s, e) => s + e.hours, 0)
                const wlAmount = entries.reduce((s, e) => s + e.amount, 0)
                const isWlExcluded = excludedWorklogs.has(worklogId)
                const isFlExcluded = excludedFreelancers.has(first.freelancer_id)
                const isExcluded = isWlExcluded || isFlExcluded

                return (
                  <TableRow
                    key={worklogId}
                    className={isExcluded ? "opacity-40" : undefined}
                  >
                    <TableCell>
                      <Checkbox
                        checked={!isWlExcluded}
                        onCheckedChange={() => onToggleWorklog(worklogId)}
                        aria-label={`Toggle worklog ${first.worklog_title}`}
                      />
                    </TableCell>
                    <TableCell className="font-medium text-sm">
                      {first.worklog_title}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-sm">
                          {first.freelancer_name ?? "—"}
                        </span>
                        <Checkbox
                          checked={!isFlExcluded}
                          onCheckedChange={() =>
                            onToggleFreelancer(first.freelancer_id)
                          }
                          aria-label={`Toggle all worklogs for ${first.freelancer_name}`}
                          title="Uncheck to exclude all worklogs for this freelancer"
                        />
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {wlHours.toFixed(2)}h
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm font-medium">
                      ${wlAmount.toFixed(2)}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}

      <div className="flex items-center justify-between rounded-md bg-muted/50 px-4 py-2 text-sm">
        <span className="text-muted-foreground">
          {included.length === batch.eligible_entries.length
            ? `All ${included.length} entries included`
            : `${included.length} of ${batch.eligible_entries.length} entries included`}
        </span>
        <span className="font-mono font-medium">
          {totalHours.toFixed(2)}h · ${totalAmount.toFixed(2)}
        </span>
      </div>

      <DialogFooter className="gap-2 sm:gap-0">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={onNext}
          disabled={included.length === 0}
          aria-label="Proceed to confirm payment"
        >
          Review & Confirm
        </Button>
      </DialogFooter>
    </div>
  )
}

// Step 3 — confirm
function StepConfirm({
  batch,
  excludedWorklogs,
  excludedFreelancers,
  onBack,
  onConfirm,
  isLoading,
}: {
  batch: PaymentBatchDetail
  excludedWorklogs: Set<string>
  excludedFreelancers: Set<string>
  onBack: () => void
  onConfirm: () => void
  isLoading: boolean
}) {
  const included = batch.eligible_entries.filter(
    (e) =>
      !excludedWorklogs.has(e.worklog_id) &&
      !excludedFreelancers.has(e.freelancer_id),
  )
  const totalAmount = included.reduce((sum, e) => sum + e.amount, 0)
  const totalHours = included.reduce((sum, e) => sum + e.hours, 0)

  const uniqueFreelancers = new Set(included.map((e) => e.freelancer_id)).size

  return (
    <div className="flex flex-col gap-6 py-4">
      <p className="text-sm text-muted-foreground">
        Review the summary below and confirm to process the payment batch.
        This action cannot be undone.
      </p>

      <dl className="grid grid-cols-2 gap-4 text-sm">
        <div className="rounded-lg border p-4">
          <dt className="text-muted-foreground">Period</dt>
          <dd className="font-medium mt-1">
            {formatDate(batch.date_from)} – {formatDate(batch.date_to)}
          </dd>
        </div>
        <div className="rounded-lg border p-4">
          <dt className="text-muted-foreground">Freelancers</dt>
          <dd className="font-medium mt-1">{uniqueFreelancers}</dd>
        </div>
        <div className="rounded-lg border p-4">
          <dt className="text-muted-foreground">Total Hours</dt>
          <dd className="font-mono font-medium mt-1">{totalHours.toFixed(2)}h</dd>
        </div>
        <div className="rounded-lg border p-4 bg-primary/5">
          <dt className="text-muted-foreground">Total Payout</dt>
          <dd className="font-mono text-lg font-bold mt-1">
            ${totalAmount.toFixed(2)}
          </dd>
        </div>
      </dl>

      <div className="flex items-center gap-2">
        <Badge variant="outline">{included.length} entries</Badge>
        {(excludedWorklogs.size > 0 || excludedFreelancers.size > 0) && (
          <Badge variant="secondary">
            {batch.eligible_entries.length - included.length} excluded
          </Badge>
        )}
      </div>

      <DialogFooter className="gap-2 sm:gap-0">
        <Button variant="outline" onClick={onBack} disabled={isLoading}>
          Back
        </Button>
        <Button
          onClick={onConfirm}
          disabled={isLoading || included.length === 0}
          aria-label="Confirm and process payment batch"
        >
          {isLoading ? "Processing…" : "Confirm Payment"}
        </Button>
      </DialogFooter>
    </div>
  )
}

// Main dialog
export function CreateBatchDialog() {
  const queryClient = useQueryClient()

  const [open, setOpen] = useState(false)
  const [step, setStep] = useState<Step>("date_range")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [batch, setBatch] = useState<PaymentBatchDetail | null>(null)
  const [excludedWorklogs, setExcludedWorklogs] = useState<Set<string>>(
    new Set(),
  )
  const [excludedFreelancers, setExcludedFreelancers] = useState<Set<string>>(
    new Set(),
  )

  const createMutation = useMutation({
    mutationFn: (data: { date_from: string; date_to: string }) =>
      PaymentsService.createBatch({
        requestBody: { date_from: data.date_from, date_to: data.date_to },
      }),
    onSuccess: (data) => {
      setBatch(data)
      setExcludedWorklogs(new Set())
      setExcludedFreelancers(new Set())
      setStep("review")
    },
    onError: () => {
      toast.error("Failed to create payment batch. Please try again.")
    },
  })

  const confirmMutation = useMutation({
    mutationFn: () => {
      if (!batch) throw new Error("No batch loaded")
      return PaymentsService.confirmBatch({
        batchId: batch.id,
        requestBody: {
          excluded_worklog_ids: Array.from(excludedWorklogs),
          excluded_freelancer_ids: Array.from(excludedFreelancers),
        },
      })
    },
    onSuccess: () => {
      toast.success("Payment batch confirmed successfully.")
      queryClient.invalidateQueries({ queryKey: ["payment-batches"] })
      handleClose()
    },
    onError: () => {
      toast.error("Failed to confirm payment batch. Please try again.")
    },
  })

  function handleClose() {
    setOpen(false)
    setStep("date_range")
    setDateFrom("")
    setDateTo("")
    setBatch(null)
    setExcludedWorklogs(new Set())
    setExcludedFreelancers(new Set())
  }

  function handleDateChange(from: string, to: string) {
    setDateFrom(from)
    setDateTo(to)
  }

  function handlePreview() {
    createMutation.mutate({ date_from: dateFrom, date_to: dateTo })
  }

  function toggleWorklog(id: string) {
    setExcludedWorklogs((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  function toggleFreelancer(id: string) {
    setExcludedFreelancers((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const stepLabel =
    step === "date_range"
      ? "Step 1 of 3 — Select Date Range"
      : step === "review"
        ? "Step 2 of 3 — Review Worklogs"
        : "Step 3 of 3 — Confirm Payment"

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button aria-label="Create a new payment batch">
          <PlusCircle className="h-4 w-4 mr-2" />
          New Payment Batch
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create Payment Batch</DialogTitle>
          <DialogDescription>{stepLabel}</DialogDescription>
        </DialogHeader>

        {step === "date_range" && (
          <StepDateRange
            dateFrom={dateFrom}
            dateTo={dateTo}
            onChange={handleDateChange}
            onNext={handlePreview}
            isLoading={createMutation.isPending}
          />
        )}

        {step === "review" && batch && (
          <StepReview
            batch={batch}
            excludedWorklogs={excludedWorklogs}
            excludedFreelancers={excludedFreelancers}
            onToggleWorklog={toggleWorklog}
            onToggleFreelancer={toggleFreelancer}
            onBack={() => setStep("date_range")}
            onNext={() => setStep("confirm")}
          />
        )}

        {step === "confirm" && batch && (
          <StepConfirm
            batch={batch}
            excludedWorklogs={excludedWorklogs}
            excludedFreelancers={excludedFreelancers}
            onBack={() => setStep("review")}
            onConfirm={() => confirmMutation.mutate()}
            isLoading={confirmMutation.isPending}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}
